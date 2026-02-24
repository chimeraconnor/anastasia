#!/usr/bin/env python3
"""
Entity & Relationship Extraction for Ana's Knowledge Graph
===========================================================
Reads all documents from QMD SQLite, extracts named entities,
builds relationships from co-occurrence + embedding similarity,
detects communities via label propagation, and outputs graph.json.

Run inside the container:
  python3 extract_graph.py

Outputs:
  graph.json — {entities, relationships, communities, meta}
"""

import json
import re
import sqlite3
import hashlib
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

import numpy as np

# ─── Config ──────────────────────────────────────────────────────────────────

DB_PATH  = Path("/home/node/.openclaw/agents/main/qmd/xdg-cache/qmd/index.sqlite")
EXT_PATH = Path("/home/node/.bun/install/global/node_modules/sqlite-vec-linux-x64/vec0.so")
OUTPUT   = Path("/home/node/.openclaw/workspace/tools/memory-dashboard/graph.json")

# Minimum co-occurrences to create an edge
MIN_COOCCURRENCE = 1
# Minimum embedding similarity to boost edge weight
EMB_SIM_THRESHOLD = 0.55
# Minimum entity mentions to include
MIN_ENTITY_MENTIONS = 1

# ─── Seed Entities ────────────────────────────────────────────────────────────
# Known entities with type and aliases. These anchor the extraction.

SEED_ENTITIES = {
    # People
    "Mr. Grey":     {"type": "person", "aliases": ["grey", "chimeraconnor", "mr grey", "mr. grey"]},
    "Anastasia":    {"type": "person", "aliases": ["ana", "anastasia steele", "anastasia"]},

    # Platforms & Tools
    "OpenClaw":     {"type": "tool", "aliases": ["openclaw"]},
    "Discord":      {"type": "platform", "aliases": ["discord"]},
    "Telegram":     {"type": "platform", "aliases": ["telegram"]},
    "GitHub":       {"type": "platform", "aliases": ["github", "git"]},
    "SearXNG":      {"type": "tool", "aliases": ["searxng", "searx"]},
    "Docker":       {"type": "tool", "aliases": ["docker", "docker compose", "container"]},
    "sherpa-onnx":  {"type": "tool", "aliases": ["sherpa-onnx", "sherpa onnx", "sherpa"]},
    "Kokoro":       {"type": "tool", "aliases": ["kokoro"]},
    "QMD":          {"type": "tool", "aliases": ["qmd"]},
    "ffmpeg":       {"type": "tool", "aliases": ["ffmpeg"]},
    "SQLite":       {"type": "tool", "aliases": ["sqlite", "sqlite3", "sqlite-vec"]},
    "Python":       {"type": "tool", "aliases": ["python", "python3", "pip"]},
    "Tailscale":    {"type": "tool", "aliases": ["tailscale"]},

    # Projects
    "Discord Voice Skill": {"type": "project", "aliases": ["discord voice", "voice skill", "send_voice.py", "discord-voice"]},
    "Memory Dashboard":    {"type": "project", "aliases": ["memory dashboard", "dashboard", "build_dashboard"]},
    "TTS System":          {"type": "project", "aliases": ["tts", "text-to-speech", "tts-speak", "voice synthesis"]},
    "Cron System":         {"type": "project", "aliases": ["cron", "cron job", "cron jobs", "scheduling"]},
    "Discord Presence":    {"type": "project", "aliases": ["presence rotation", "discord presence", "set-presence"]},
    "Morning Greeting":    {"type": "project", "aliases": ["morning greeting", "daily greeting", "daily-anastasia-greeting"]},
    "Self-Improving Agent":{"type": "project", "aliases": ["self-improving", "learning review"]},

    # Key Files
    "MEMORY.md":    {"type": "file", "aliases": ["memory.md"]},
    "SOUL.md":      {"type": "file", "aliases": ["soul.md"]},
    "TOOLS.md":     {"type": "file", "aliases": ["tools.md"]},
    "AGENTS.md":    {"type": "file", "aliases": ["agents.md"]},
    "PROJECTS.md":  {"type": "file", "aliases": ["projects.md"]},
    "HEARTBEAT.md": {"type": "file", "aliases": ["heartbeat.md"]},
    "IDENTITY.md":  {"type": "file", "aliases": ["identity.md"]},
    "USER.md":      {"type": "file", "aliases": ["user.md"]},

    # Concepts
    "Heartbeat":         {"type": "concept", "aliases": ["heartbeat", "heartbeat-state"]},
    "Memory Search":     {"type": "concept", "aliases": ["memory search", "memory_search", "semantic search"]},
    "Embeddings":        {"type": "concept", "aliases": ["embeddings", "embedding", "vectors", "vector"]},
    "Voice Messages":    {"type": "concept", "aliases": ["voice message", "voice messages", "audio message"]},
    "Session Management":{"type": "concept", "aliases": ["session", "sessions", "compaction"]},
    "Waveform":          {"type": "concept", "aliases": ["waveform", "waveform visualization"]},
    "Thread-Bound Sessions": {"type": "concept", "aliases": ["thread-bound", "thread sessions"]},
    "Open-Antigravity":  {"type": "concept", "aliases": ["open-antigravity", "antigravity"]},
    "OGG/Opus":          {"type": "concept", "aliases": ["ogg", "opus", "ogg/opus"]},
    "API Flow":          {"type": "concept", "aliases": ["api flow", "3-step", "discord api"]},
}

TYPE_COLORS = {
    "person":   "#FF6B6B",
    "tool":     "#45B7D1",
    "platform": "#9B59B6",
    "project":  "#F39C12",
    "file":     "#2ECC71",
    "concept":  "#E74C3C",
    "lesson":   "#FF8C42",
    "topic":    "#00CEC9",
}

# ─── Load Data ────────────────────────────────────────────────────────────────

def load_documents() -> List[Dict]:
    """Load all active documents from QMD."""
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("""
        SELECT d.collection, d.path, d.title, d.hash, d.created_at,
               c.doc
        FROM documents d
        JOIN content c ON d.hash = c.hash
        WHERE d.active = 1
        ORDER BY d.created_at
    """)
    docs = []
    for col, path, title, hash_, created_at, doc in cur.fetchall():
        docs.append(dict(
            collection=col, path=path, title=title,
            hash=hash_, created_at=created_at, text=doc,
        ))
    conn.close()
    return docs


def load_embeddings() -> Dict[str, np.ndarray]:
    """Load chunk embeddings from vectors_vec."""
    conn = sqlite3.connect(str(DB_PATH))
    conn.enable_load_extension(True)
    conn.load_extension(str(EXT_PATH))
    cur = conn.cursor()
    cur.execute("SELECT hash_seq, embedding FROM vectors_vec")
    emb = {}
    for hs, blob in cur.fetchall():
        emb[hs] = np.frombuffer(blob, dtype=np.float32).copy()
    conn.close()
    return emb


def load_chunk_positions() -> Dict[str, List[Tuple[int, int]]]:
    """Load chunk positions per document hash."""
    conn = sqlite3.connect(str(DB_PATH))
    cur = conn.cursor()
    cur.execute("SELECT hash, seq, pos FROM content_vectors ORDER BY hash, seq")
    positions = defaultdict(list)
    for h, seq, pos in cur.fetchall():
        positions[h].append((seq, pos))
    conn.close()
    return positions


# ─── Entity Extraction ────────────────────────────────────────────────────────

class EntityExtractor:
    def __init__(self):
        # Build lookup: lowercase alias -> canonical name
        self.alias_map: Dict[str, str] = {}
        self.entity_meta: Dict[str, Dict] = {}

        for name, info in SEED_ENTITIES.items():
            canon = name
            self.entity_meta[canon] = {
                "type": info["type"],
                "aliases": info.get("aliases", []),
            }
            # Map all aliases to canonical
            for alias in info.get("aliases", []):
                self.alias_map[alias.lower()] = canon
            self.alias_map[name.lower()] = canon

    def extract_lessons(self, text: str) -> List[Dict]:
        """Extract lesson headings from MEMORY.md format."""
        lessons = []
        pat = re.compile(r'^###\s+(.+?)\s*\((\d{4}-\d{2}-\d{2})\)', re.MULTILINE)
        for m in pat.finditer(text):
            title = m.group(1).strip()
            date = m.group(2)
            lessons.append({"name": title, "type": "lesson", "date": date})
        return lessons

    def extract_topics(self, text: str) -> List[Dict]:
        """Extract topic headings from daily notes."""
        topics = []
        pat = re.compile(r'^##\s+(?!Personal|Conversations)(.+?)$', re.MULTILINE)
        for m in pat.finditer(text):
            title = m.group(1).strip()
            if len(title) < 4 or title.startswith("#"):
                continue
            if re.match(r'^\d{4}', title):  # Skip date headings
                continue
            topics.append({"name": title, "type": "topic"})

        # Also get ### subheadings
        pat2 = re.compile(r'^###\s+(.+?)$', re.MULTILINE)
        for m in pat2.finditer(text):
            title = m.group(1).strip()
            if len(title) < 4 or re.match(r'^\d{4}', title):
                continue
            # Skip if it's a lesson heading (has date in parens)
            if re.search(r'\(\d{4}-\d{2}-\d{2}\)$', title):
                continue
            topics.append({"name": title, "type": "topic"})
        return topics

    def extract_from_doc(self, doc: Dict) -> Tuple[Set[str], List[Dict]]:
        """
        Extract entity mentions from a document.
        Returns (set of canonical entity names found, list of new entities discovered).
        """
        text = doc["text"]
        text_lower = text.lower()
        found: Set[str] = set()
        new_entities: List[Dict] = []

        # 1. Match seed entities
        for alias, canon in self.alias_map.items():
            # Word boundary match
            if re.search(r'(?<![a-zA-Z])' + re.escape(alias) + r'(?![a-zA-Z])', text_lower):
                found.add(canon)

        # 2. Extract lessons (from MEMORY.md)
        if doc["collection"] in ("memory-root-main", "memory-alt-main"):
            for lesson in self.extract_lessons(text):
                name = lesson["name"]
                if name not in self.entity_meta:
                    self.entity_meta[name] = {"type": "lesson", "date": lesson.get("date")}
                    self.alias_map[name.lower()] = name
                    new_entities.append(lesson)
                found.add(name)

        # 3. Extract topics from daily notes
        if doc["collection"] == "memory-dir-main" and re.match(r'^\d{4}-\d{2}-\d{2}\.md$', doc["path"]):
            for topic in self.extract_topics(text):
                name = topic["name"]
                if name not in self.entity_meta and len(name) < 60:
                    self.entity_meta[name] = {"type": "topic"}
                    self.alias_map[name.lower()] = name
                    new_entities.append(topic)
                found.add(name)

        # 4. Extract topics from session transcripts (Assistant's structured responses)
        if doc["collection"] == "sessions-main":
            # Look for ## headings in assistant responses
            for topic in self.extract_topics(text):
                name = topic["name"]
                if name not in self.entity_meta and len(name) < 60:
                    self.entity_meta[name] = {"type": "topic"}
                    self.alias_map[name.lower()] = name
                    new_entities.append(topic)
                found.add(name)

        return found, new_entities

    def extract_from_chunk(self, chunk_text: str) -> Set[str]:
        """Extract entity mentions from a single chunk."""
        text_lower = chunk_text.lower()
        found: Set[str] = set()
        for alias, canon in self.alias_map.items():
            if re.search(r'(?<![a-zA-Z])' + re.escape(alias) + r'(?![a-zA-Z])', text_lower):
                found.add(canon)
        return found


# ─── Relationship Building ────────────────────────────────────────────────────

def build_relationships(
    docs: List[Dict],
    chunk_positions: Dict[str, List[Tuple[int, int]]],
    embeddings: Dict[str, np.ndarray],
    extractor: EntityExtractor,
) -> Tuple[Dict[str, Dict], List[Dict]]:
    """
    Build entity nodes and relationship edges.

    Returns:
        entities: {name: {type, mentions, sources, first_seen, ...}}
        relationships: [{source, target, weight, description, ...}]
    """
    entities: Dict[str, Dict] = {}
    cooccurrence: Counter = Counter()  # (entityA, entityB) -> count
    edge_descriptions: Dict[Tuple[str, str], List[str]] = defaultdict(list)
    entity_chunk_embeddings: Dict[str, List[np.ndarray]] = defaultdict(list)

    for doc in docs:
        text = doc["text"]
        hash_ = doc["hash"]
        date = doc["created_at"][:10] if doc["created_at"] else "unknown"

        # Get chunk positions for this doc
        positions = sorted(chunk_positions.get(hash_, []), key=lambda x: x[0])

        # Process each chunk
        for i, (seq, pos) in enumerate(positions):
            next_pos = positions[i + 1][1] if i + 1 < len(positions) else len(text)
            chunk_text = text[pos:next_pos].strip()
            if not chunk_text:
                continue

            # Find entities in this chunk
            chunk_entities = extractor.extract_from_chunk(chunk_text)

            # Update entity metadata
            for ent_name in chunk_entities:
                if ent_name not in entities:
                    meta = extractor.entity_meta.get(ent_name, {})
                    entities[ent_name] = {
                        "type": meta.get("type", "concept"),
                        "mentions": 0,
                        "sources": set(),
                        "first_seen": date,
                        "chunks": [],
                        "date": meta.get("date"),
                    }
                entities[ent_name]["mentions"] += 1
                entities[ent_name]["sources"].add(doc["path"])
                if date < entities[ent_name]["first_seen"]:
                    entities[ent_name]["first_seen"] = date

                # Store chunk embedding for this entity
                emb_key = f"{hash_}_{seq}"
                if emb_key in embeddings:
                    entity_chunk_embeddings[ent_name].append(embeddings[emb_key])

            # Build co-occurrence edges
            ent_list = sorted(chunk_entities)
            for a_idx, a in enumerate(ent_list):
                for b in ent_list[a_idx + 1:]:
                    key = (a, b) if a < b else (b, a)
                    cooccurrence[key] += 1

                    # Extract a brief context snippet
                    if len(edge_descriptions[key]) < 3:
                        # Find a short sentence mentioning both
                        snippet = chunk_text[:200].replace("\n", " ").strip()
                        if snippet and snippet not in edge_descriptions[key]:
                            edge_descriptions[key].append(snippet)

    # Compute entity centroid embeddings for similarity boosting
    entity_centroids: Dict[str, np.ndarray] = {}
    for name, emb_list in entity_chunk_embeddings.items():
        if emb_list:
            entity_centroids[name] = np.mean(emb_list, axis=0)

    # Build relationship list
    relationships = []
    for (a, b), count in cooccurrence.items():
        if count < MIN_COOCCURRENCE:
            continue
        if a not in entities or b not in entities:
            continue

        # Base weight from co-occurrence
        weight = min(count / 5.0, 1.0)  # Normalize to 0-1

        # Boost with embedding similarity
        if a in entity_centroids and b in entity_centroids:
            ca, cb = entity_centroids[a], entity_centroids[b]
            sim = float(np.dot(ca, cb) / (np.linalg.norm(ca) * np.linalg.norm(cb) + 1e-10))
            if sim > EMB_SIM_THRESHOLD:
                weight = min(weight + (sim - EMB_SIM_THRESHOLD) * 0.5, 1.0)

        desc = edge_descriptions.get((a, b), [""])
        relationships.append({
            "source": a,
            "target": b,
            "weight": round(weight, 3),
            "cooccurrences": count,
            "description": desc[0][:200] if desc else "",
        })

    # Convert sets to lists for JSON
    for ent in entities.values():
        ent["sources"] = sorted(ent["sources"])
        ent.pop("chunks", None)

    return entities, relationships


# ─── Community Detection (Label Propagation) ─────────────────────────────────

def detect_communities(
    entities: Dict[str, Dict],
    relationships: List[Dict],
    max_communities: int = 12,
) -> Dict[str, int]:
    """
    Simple label propagation for community detection.
    Returns {entity_name: community_id}.
    """
    if not relationships:
        return {name: 0 for name in entities}

    # Build adjacency list with weights
    adj: Dict[str, List[Tuple[str, float]]] = defaultdict(list)
    for rel in relationships:
        s, t, w = rel["source"], rel["target"], rel["weight"]
        adj[s].append((t, w))
        adj[t].append((s, w))

    # Initialize: each node is its own community
    labels = {name: i for i, name in enumerate(entities)}
    name_list = list(entities.keys())

    # Iterate
    import random
    rng = random.Random(42)
    for _ in range(50):
        changed = False
        rng.shuffle(name_list)
        for node in name_list:
            if node not in adj:
                continue
            # Count weighted votes from neighbors
            votes: Counter = Counter()
            for neighbor, weight in adj[node]:
                votes[labels[neighbor]] += weight
            if votes:
                best = votes.most_common(1)[0][0]
                if best != labels[node]:
                    labels[node] = best
                    changed = True
        if not changed:
            break

    # Renumber communities starting from 0
    unique_labels = sorted(set(labels.values()))
    remap = {old: new for new, old in enumerate(unique_labels)}
    labels = {name: remap[lab] for name, lab in labels.items()}

    # If too many communities, merge small ones
    community_sizes = Counter(labels.values())
    if len(community_sizes) > max_communities:
        # Keep top N-1, merge rest into "other"
        top = {c for c, _ in community_sizes.most_common(max_communities - 1)}
        other_id = max(top) + 1 if top else 0
        labels = {name: (cid if cid in top else other_id) for name, cid in labels.items()}
        # Renumber again
        unique = sorted(set(labels.values()))
        remap = {old: new for new, old in enumerate(unique)}
        labels = {name: remap[lab] for name, lab in labels.items()}

    return labels


def generate_community_summaries(
    entities: Dict[str, Dict],
    communities: Dict[str, int],
) -> List[Dict]:
    """Generate a summary for each community based on its members."""
    comm_members: Dict[int, List[str]] = defaultdict(list)
    for name, cid in communities.items():
        comm_members[cid].append(name)

    summaries = []
    for cid in sorted(comm_members.keys()):
        members = comm_members[cid]
        # Find dominant type
        type_counts = Counter(entities[m]["type"] for m in members if m in entities)
        dominant = type_counts.most_common(1)[0][0] if type_counts else "mixed"

        # Find most mentioned entity as label
        top_entity = max(members, key=lambda m: entities.get(m, {}).get("mentions", 0))

        # Generate label from top entities
        top_names = sorted(members, key=lambda m: -entities.get(m, {}).get("mentions", 0))[:4]
        label = " / ".join(top_names)

        summaries.append({
            "id": cid,
            "label": label,
            "dominant_type": dominant,
            "size": len(members),
            "members": sorted(members),
        })

    return summaries


# ─── Main ─────────────────────────────────────────────────────────────────────

def main():
    print("Extracting knowledge graph from QMD...")

    # Load data
    print("  -> Loading documents...")
    docs = load_documents()
    print(f"  -> {len(docs)} documents")

    print("  -> Loading embeddings...")
    embeddings = load_embeddings()
    print(f"  -> {len(embeddings)} vectors")

    print("  -> Loading chunk positions...")
    chunk_positions = load_chunk_positions()

    # Initialize extractor and do first pass (discover entities from structure)
    print("  -> Extracting entities...")
    extractor = EntityExtractor()

    # First pass: discover new entities from document structure
    for doc in docs:
        extractor.extract_from_doc(doc)

    # Build entities and relationships
    print("  -> Building relationships...")
    entities, relationships = build_relationships(
        docs, chunk_positions, embeddings, extractor
    )

    # Filter low-mention entities
    entities = {k: v for k, v in entities.items() if v["mentions"] >= MIN_ENTITY_MENTIONS}

    # Filter relationships to only include remaining entities
    relationships = [r for r in relationships
                     if r["source"] in entities and r["target"] in entities]

    print(f"  -> {len(entities)} entities, {len(relationships)} relationships")

    # Detect communities
    print("  -> Detecting communities...")
    communities = detect_communities(entities, relationships)

    # Assign community to entities
    for name, cid in communities.items():
        if name in entities:
            entities[name]["community"] = cid

    # Generate community summaries
    community_summaries = generate_community_summaries(entities, communities)
    print(f"  -> {len(community_summaries)} communities detected")

    # Build output
    nodes = []
    for name, meta in entities.items():
        nodes.append({
            "id": name,
            "name": name,
            "type": meta["type"],
            "color": TYPE_COLORS.get(meta["type"], "#888888"),
            "mentions": meta["mentions"],
            "sources": meta["sources"],
            "first_seen": meta["first_seen"],
            "community": meta.get("community", 0),
            "date": meta.get("date"),
        })

    # Sort by mentions descending
    nodes.sort(key=lambda n: -n["mentions"])

    # Generate type stats
    type_stats = Counter(n["type"] for n in nodes)

    graph = {
        "nodes": nodes,
        "links": relationships,
        "communities": community_summaries,
        "meta": {
            "generated_at": datetime.now().isoformat(),
            "total_documents": len(docs),
            "total_embeddings": len(embeddings),
            "total_entities": len(nodes),
            "total_relationships": len(relationships),
            "total_communities": len(community_summaries),
            "type_stats": dict(type_stats),
            "type_colors": TYPE_COLORS,
        },
    }

    # Write output
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    OUTPUT.write_text(json.dumps(graph, indent=2, ensure_ascii=False), encoding="utf-8")

    size_kb = OUTPUT.stat().st_size // 1024
    print(f"\n  Done! {size_kb} KB -> {OUTPUT}")
    print(f"  Entities: {len(nodes)}")
    for t, c in type_stats.most_common():
        print(f"    {t}: {c}")
    print(f"  Relationships: {len(relationships)}")
    print(f"  Communities: {len(community_summaries)}")


if __name__ == "__main__":
    main()
