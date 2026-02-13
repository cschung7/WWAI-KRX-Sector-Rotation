# InfraNodus-Style Theme Network Visualization

## Overview

The Theme Network (`/theme-network.html`) is an InfraNodus-inspired force-directed network visualization showing co-occurrence relationships between KRX Naver themes. Themes that share many stocks cluster together, revealing structural patterns in the Korean stock market's thematic landscape.

**Live URL**: https://krx.wwai.app/theme-network.html

---

## Architecture

```
┌─────────────────────────────────────────────────────────────────────┐
│  Browser (theme-network.html)                                       │
│                                                                     │
│  ┌─────────────┐    ┌─────────────┐    ┌──────────┐    ┌─────────┐ │
│  │ Fetch API   │───▶│ Graph Algos │───▶│ FA2      │───▶│ Canvas  │ │
│  │ Co-occur    │    │ Louvain +   │    │ Layout   │    │ Render  │ │
│  │ Endpoint    │    │ Betweenness │    │ (500 fr) │    │ + UI    │ │
│  └─────────────┘    └─────────────┘    └──────────┘    └─────────┘ │
│         │                                                    │      │
│         │                                              ┌─────┴────┐ │
│         │                                              │ Sidebar  │ │
│         │                                              │ Topics   │ │
│         │                                              │ Insights │ │
│         │                                              │ Search   │ │
│         │                                              └──────────┘ │
└─────────┼───────────────────────────────────────────────────────────┘
          │
          ▼
┌─────────────────────────────────────────────────────────────────────┐
│  Backend (FastAPI port 8000)                                        │
│                                                                     │
│  GET /api/network/theme-cooccurrence                                │
│    ?min_stocks=5 &min_shared=4 &max_themes=60                       │
│                                                                     │
│  ┌────────────────┐    ┌──────────────────┐    ┌──────────────────┐ │
│  │ network_theme  │───▶│ theme→stocks map │───▶│ pairwise set     │ │
│  │ _data.csv      │    │ (2922 stocks,    │    │ intersection     │ │
│  │                │    │  266 themes)     │    │ → edges          │ │
│  └────────────────┘    └──────────────────┘    └──────────────────┘ │
│                                                                     │
│  + naver_themes_weekly_fiedler_2025.csv  (Fiedler scores per theme) │
└─────────────────────────────────────────────────────────────────────┘
```

---

## Data Pipeline

### 1. Backend: Co-occurrence Network Construction

**File**: `dashboard/backend/routers/network.py`
**Endpoint**: `GET /api/network/theme-cooccurrence`

#### Step 1: Load Theme Data

Source: `data/network_theme_data.csv` (local copy of NaverTheme `db_final.csv`)

Each row is a stock with columns including:
- `name`: Korean stock name (e.g., 삼성전자)
- `naverTheme`: Python list literal of theme memberships (e.g., `['반도체', '2차전지']`)
- `tickers`: 6-digit KRX ticker code
- `-1`, `0`, `1`: Signal probabilities (sell/neutral/buy)

#### Step 2: Build Theme-to-Stocks Mapping

```python
theme_stocks_map = {}  # theme_name → set of stock_names
for each stock in CSV:
    themes = parse_themes(stock.naverTheme)  # ast.literal_eval
    for theme in themes:
        theme_stocks_map[theme].add(stock.name)
```

This produces ~266 themes, each mapping to a set of stock names.

#### Step 3: Filter by Minimum Stock Count

```python
valid_themes = {t: stocks for t, stocks in theme_stocks_map.items()
                if len(stocks) >= min_stocks}  # default: 5
```

Themes with fewer than `min_stocks` members are excluded (too sparse for meaningful co-occurrence).

#### Step 4: Select Top N Themes

```python
sorted_themes = sorted(valid_themes.keys(),
                       key=lambda t: len(valid_themes[t]), reverse=True)
selected = sorted_themes[:max_themes]  # default: 60
```

Themes are ranked by stock count (descending). Only the top `max_themes` are included to keep the graph readable.

#### Step 5: Compute Pairwise Co-occurrence (Edge Weight)

**Edge weight = number of stocks that belong to both themes simultaneously** (set intersection size).

This is the only metric driving the entire network. There is no derived formula — it is a raw count of shared membership.

**Concrete Example**:

```
Theme "반도체 장비" member stocks: {삼성전자, SK하이닉스, 한미반도체, 원익IPS, ...}  (52 stocks)
Theme "2차전지"     member stocks: {삼성전자, SK이노베이션, LG에너지솔루션, ...}     (162 stocks)

Set intersection: {삼성전자, ...} → 13 stocks appear in BOTH themes

Edge weight = 13
```

**Source data**: Each stock in `network_theme_data.csv` has a `naverTheme` column listing its theme memberships as a Python list literal:

```csv
name,        naverTheme,                              tickers
삼성전자,     "['반도체', '2차전지', '5G', ...]",       005930
SK하이닉스,   "['반도체', '반도체 장비', 'HBM', ...]",  000660
```

A single stock belonging to N themes creates co-occurrence between all C(N,2) theme pairs it connects.

**Backend computation**:

```python
# Build theme → set of stock names
theme_stocks = {
    "반도체":      {"삼성전자", "SK하이닉스", "한미반도체", ...},   # 87 stocks
    "2차전지":     {"삼성전자", "LG에너지솔루션", ...},            # 162 stocks
    "반도체 장비":  {"SK하이닉스", "한미반도체", "원익IPS", ...},   # 52 stocks
    ...  # 266 themes total
}

# For every pair, count overlap
for i in range(len(selected)):
    for j in range(i+1, len(selected)):
        shared = len(theme_stocks[t1] & theme_stocks[t2])  # set intersection
        if shared >= min_shared:  # default: 4
            edges.append({source: i, target: j, weight: shared})
```

**Filtering thresholds**:

| Parameter | Default | Effect |
|-----------|---------|--------|
| `min_stocks` | 5 | Theme needs ≥5 member stocks to appear as a node |
| `min_shared` | 4 | Two themes need ≥4 shared stocks for an edge to exist |
| `max_themes` | 60 | Only top 60 themes by stock count are included |

With defaults, this typically produces ~60 nodes and ~450 edges.

**Frontend normalization** (for rendering only — does not affect graph algorithms):

```javascript
maxW = max(all raw edge weights)              // e.g. 45
normalized_w = raw_weight / maxW              // → [0, 1]

// Visual mapping:
edge_opacity = 0.06 + normalized_w * 0.22     // range: 0.06 → 0.28
edge_width   = (0.4 + normalized_w * 1.8) / cam.s  // range: 0.4px → 2.2px (world-space)
```

**Interpretation**: A high edge weight means two themes draw from the same pool of stocks, suggesting they are structurally related (e.g., "반도체" and "반도체 장비" share many semiconductor companies). A low or zero weight means the themes have distinct stock universes.

#### Step 6: Attach Fiedler Scores

Each node gets a `fiedler` value from `naver_themes_weekly_fiedler_2025.csv` (latest date), representing the theme's internal cohesion (connectivity of its member stocks' correlation network).

#### Response Format

```json
{
  "nodes": [
    {"id": 0, "code": "자동차부품", "label": "자동차부품", "fiedler": 8.371, "n_stocks": 162},
    {"id": 1, "code": "2차전지", "label": "2차전지", "fiedler": 7.51, "n_stocks": 162}
  ],
  "edges": [
    {"source": 0, "target": 1, "weight": 13}
  ],
  "stats": {
    "node_count": 60, "edge_count": 451,
    "total_themes": 266, "min_stocks": 5, "min_shared": 4
  }
}
```

**Caching**: Results are cached with daily TTL invalidation (`_cooccurrence_cache`). Cache key includes all query parameters.

---

### 2. Frontend: Graph Algorithms

**File**: `dashboard/frontend/theme-network.html` (lines 324-414)

All algorithms run **client-side in pure JavaScript** with zero dependencies.

#### 2a. Adjacency Matrix

```javascript
adj = Array(n x n, fill 0)
for each edge:
    adj[source][target] = weight
    adj[target][source] = weight   // symmetric
maxW = max(all weights)
fa2Edges = edges.map(e => ({s, t, w: weight/maxW, raw: weight}))
```

Weights are normalized to [0, 1] for the FA2 engine. Raw weights preserved for display.

#### 2b. Louvain Community Detection

Single-pass modularity optimization (15 iteration cap). Assigns each node to a community that maximizes modularity gain.

**Algorithm**:

1. Initialize: each node in its own community
2. Compute total weight `tw = sum(adj[i][j])` for all pairs
3. For each iteration:
   - For each node `i`:
     - Compute modularity gain of moving `i` to each neighbor's community
     - Modularity gain: `deltaQ = ki_in - sTot * ki / (2 * m)`
       - `ki_in` = sum of weights from `i` to nodes in target community
       - `sTot` = total degree of target community
       - `ki` = degree of node `i`
       - `m` = total edge weight
     - Move `i` to community with highest positive gain
   - Stop when no moves improve modularity
4. Remap community IDs to contiguous 0..K-1

**Output**: `communities[i]` = community index for node `i` (typically 3-6 clusters)

**Complexity**: O(n^2) per iteration, converges in <5 iterations for 60 nodes (~<1ms)

#### 2c. Betweenness Centrality (Brandes' Algorithm)

Measures how often a node lies on shortest paths between other nodes. High centrality = "bridge" or "connector" theme.

**Algorithm**:

```
For each source s in [0..n):
    BFS from s, recording:
      - sigma[v] = number of shortest paths from s to v
      - pred[v]  = predecessors on shortest paths
      - dist[v]  = shortest distance
    Back-propagate dependencies:
      for v in reverse BFS order:
        for u in pred[v]:
          delta[u] += (sigma[u] / sigma[v]) * (1 + delta[v])
        bc[v] += delta[v]

Normalize: bc[i] /= max(bc)  → [0, 1]
```

Edges with `adj[v][w] < threshold` (default 0.5) are excluded from BFS traversal. This prevents weak connections from dominating path calculations.

**Complexity**: O(V * E) ≈ O(60 * 451) ≈ 27K operations (<1ms)

**Output**: `centralities[i]` in [0, 1], where 1 = highest centrality node

---

### 3. Frontend: ForceAtlas2 Layout Engine

**File**: `dashboard/frontend/theme-network.html` (lines 371-414)

ForceAtlas2 is a continuous force-directed layout algorithm designed for real-world networks. It uses LinLog mode for better community separation.

#### Configuration

```javascript
const cfg = { sr: 3, g: 3, att: 0.1 };
const TOTAL_FRAMES = 500;
const minSep = 30;  // minimum pixel separation between nodes
```

| Parameter | Value | Description |
|-----------|-------|-------------|
| `sr` | 3 | Scaling ratio — repulsion strength multiplier |
| `g` | 3 | Gravity — pulls all nodes toward centroid |
| `att` | 0.1 | Attraction multiplier along edges |
| `TOTAL_FRAMES` | 500 | Total simulation steps (synchronous) |
| `minSep` | 30 | Minimum distance between any two nodes |

#### Forces

**Repulsion** (all node pairs, O(n^2)):
```
For each pair (i, j):
    d = euclidean_distance(i, j)
    force = sr * phase_mult * (mass_i + 1)(mass_j + 1) / d^2
    direction: push apart along (j - i) vector
```
Where `mass = degree + 1` (number of connections + 1).

**Attraction** (edges only):
```
For each edge (s, t):
    d = euclidean_distance(s, t)
    force = d * normalized_weight * att
    direction: pull together along (t - s) vector
```
Linear attraction (not log): `f = d * w * att`.

**Gravity** (centroid-based):
```
centroid = mean of all node positions
For each node i:
    force = (pos_i - centroid) * g * 0.01
    direction: toward centroid
```
Gravity uses the **centroid of all nodes** (not screen center), preventing drift when zoom/pan changes.

#### 3-Phase Convergence

```javascript
const p = frame / totalFrames;  // progress 0→1
const pm = p < 0.15 ? 1.5      // Phase 1: fast separation (0-15%)
         : p < 0.50 ? 1.0      // Phase 2: normal settling (15-50%)
         : 0.5;                 // Phase 3: fine-tune (50-100%)
// pm scales the repulsion force
```

| Phase | Frames | Repulsion | Purpose |
|-------|--------|-----------|---------|
| Fast | 0-75 | 1.5x | Separate overlapping nodes quickly |
| Normal | 75-250 | 1.0x | Natural force equilibrium |
| Fine-tune | 250-500 | 0.5x | Stabilize positions, reduce jitter |

#### Adaptive Speed Control

Each node has an individual speed based on oscillation detection:

```javascript
swing = |current_force - previous_force|     // direction change
traction = |current_force + previous_force|/2 // consistent direction
convergence = min(1, traction / (swing + 0.01))

global_speed = min(total_traction / (total_swing + 0.01), 5)
displacement = min(global_speed * convergence * force_magnitude, 8) / force_magnitude
position += force * displacement
```

Nodes that oscillate (high swing) move slowly; nodes with consistent force direction (high traction) move faster. Maximum displacement per frame is capped at 8 pixels.

#### Overlap Prevention

```javascript
for each pair (i, j):
    if distance(i, j) < minSep:
        push = (minSep - distance) * 0.3
        separate nodes along connecting vector by push amount
```

#### Pre-Computation

All 500 FA2 frames run **synchronously** during `init()`, before the first render. The user sees the final converged layout immediately — no animation on page load.

```javascript
for (let f = 0; f < TOTAL_FRAMES; f++) {
    fa2Step(fa2Nodes, fa2Edges, cfg, f, TOTAL_FRAMES);
}
fitView();  // auto-frame all nodes
draw();     // first and only render call
```

#### Initial Positions

Nodes start in a circular arrangement with slight randomization:

```javascript
angle = (i / n) * 2 * PI + random * 0.3
radius = 50 + random * 100
x = cos(angle) * radius
y = sin(angle) * radius
```

---

### 4. Frontend: Canvas Rendering

**File**: `dashboard/frontend/theme-network.html` (lines 520-616)

The visualization uses HTML5 Canvas 2D with HiDPI support.

#### Layout

```
┌──────────────────────────────────────────────────────────────────┐
│ Header (41px) — Nav links + Stats badge + Language toggle        │
├──────────────────────────────────────────────────────┬───────────┤
│                                                      │           │
│              Canvas Graph Area                       │  Sidebar  │
│              (flex: 1)                               │  (320px)  │
│                                                      │           │
│   Nodes rendered as colored dots with glow halos     │  Tabs:    │
│   Edges rendered as colored lines                    │  Topics   │
│   Text labels in screen-space (fixed px sizes)       │  Insights │
│                                                      │  Search   │
│                                                      │           │
│  [+][-][⟳] controls (bottom-left)                   │           │
│                                                      │           │
└──────────────────────────────────────────────────────┴───────────┘
```

#### Camera System

```javascript
cam = { x: 0, y: 0, s: 1 }  // translate x, translate y, scale
```

- **Pan**: Background drag → updates `cam.x`, `cam.y`
- **Zoom**: Mouse wheel → scales `cam.s` (range 0.3 to 6.0), zoom toward cursor
- **Node drag**: Drag specific node → updates `fa2Nodes[i].x/y` in world-space
- **fitView()**: Computes bounding box of all nodes, sets camera to frame them with 60px padding

#### Rendering Layers (draw order)

1. **Background**: Solid fill `#0a0a12`
2. **Edges** (world-space transform):
   - Same-cluster edges: community color at `0.06 + w * 0.22` opacity
   - Cross-cluster edges: `#3a3a5a` at same opacity formula
   - Line width: `(0.4 + w * 1.8) / cam.s` — thinner when zoomed in
   - When cluster or search is active: highlighted edges get +0.15 opacity, others dimmed to 15%
3. **Node dots** (world-space transform):
   - Glow halo: radial gradient `(community_color, 45% → 0%)` at radius `3x dot`
   - Dot fill: solid community color at radius `(3 + bc * 8) / cam.s`
   - Dimmed nodes get `globalAlpha = 0.2`
4. **Text labels** (screen-space — constant pixel size regardless of zoom):
   - Font size: `9 + 27 * sqrt(bc)` pixels (9px min, 36px max)
   - Color: community color at opacity `0.3 + 0.7 * bc^0.3`
   - Font weight: 700 (bc > 0.3), 600 (bc > 0.1), 500 (others)
   - Long labels truncated: `...` at 7 chars if fontSize < 14, 11 chars if < 20
   - Position: centered above dot, offset by dot radius + 3px
5. **Hover highlight** (screen-space):
   - Ring around hovered node: `(community_color, 80% opacity)`, 2px stroke
   - Connected edges: redrawn at 50% opacity, 2px width
   - Label redrawn at full size (min 16px) and full opacity

#### Color Palette

```javascript
const COLORS = ['#4ecdc4', '#ffe66d', '#ff6b6b', '#a29bfe', '#fd79a8', '#55efc4', '#fdcb6e', '#e17055'];
//               Teal      Gold      Coral     Lavender   Pink       Mint      Amber     Terracotta
```

8 colors cycling by community index: `COLORS[community % 8]`

#### Visual Sizing Formulas

| Element | Formula | Range | Driven By |
|---------|---------|-------|-----------|
| Dot radius | `(3 + bc * 8) / cam.s` | 3-11px world | Betweenness centrality |
| Glow radius | `dotR * 3` | 9-33px world | Betweenness centrality |
| Font size | `9 + 27 * sqrt(bc)` | 9-36px screen | Betweenness centrality |
| Font opacity | `0.3 + 0.7 * bc^0.3` | 0.3-1.0 | Betweenness centrality |
| Edge opacity | `0.06 + w * 0.22` | 0.06-0.28 | Normalized weight |
| Edge width | `(0.4 + w * 1.8) / cam.s` | 0.4-2.2px world | Normalized weight |

---

### 5. Sidebar Panel

Three-tab analytics panel on the right side (320px fixed width).

#### Topics Tab

Shows cluster structure cards, one per Louvain community:

```
┌──────────────────────────────────┐
│ ● Cluster A              12 themes│  ← color-coded by community
│ 자동차부품, 2차전지, 지주사,       │  ← top 5 by centrality
│ 코리아밸류업, 시가배당률높은주      │
└──────────────────────────────────┘
```

- Sorted by member count (largest cluster first)
- Top 5 themes per cluster shown (sorted by betweenness centrality)
- Click a card → highlights that cluster in the graph (dims all others)
- Click again → deselects (shows all)

#### Insights Tab

Two sections:

**Key Connector Themes** — Top 8 nodes by betweenness centrality:

```
● 자동차부품     87%   ← centrality percentage
● 2차전지        72%
● 코리아밸류업    65%
```

These are themes that bridge multiple clusters. Click to pan the camera to that node and highlight its neighborhood.

**Structural Gaps** — Cluster pairs with the fewest inter-cluster edges:

```
┌──────────────────────────────────┐
│  ● Cluster C  ↔  ● Cluster E    │
│  2 connections                    │
└──────────────────────────────────┘
```

Gaps identify cluster pairs that are structurally disconnected — potential arbitrage or rotation blind spots.

Gap computation:
```javascript
for each pair of communities (i, j):
    count edges where source.community == i AND target.community == j
sort by count ascending → top 3 weakest pairs
```

#### Search Tab

- Live text input filtering
- Matches against `node.code` (theme name) and `node.label`
- Case-insensitive substring match
- Results sorted by centrality (most important matches first)
- Matching nodes are highlighted in the graph; non-matches dimmed
- Click a result → pans camera to that node and highlights its neighbors

---

### 6. Interactions

| Action | Trigger | Effect |
|--------|---------|--------|
| Pan | Drag background | Translates camera (`cam.x`, `cam.y`) |
| Zoom | Mouse wheel | Scales camera toward cursor (`cam.s`, range 0.3-6.0) |
| Drag node | Drag dot | Moves node in world-space |
| Hover | Mouse over node | Shows ring highlight + tooltip + connected edges |
| Tooltip | Hover | Fixed-position tooltip: name, cluster, centrality bar, connections, Fiedler, stock count |
| Select cluster | Click cluster card | Dims all other clusters; click again to deselect |
| Search highlight | Type in search | Highlights matching nodes, dims others |
| Pan to node | Click insight/search item | Centers camera on that node, highlights neighborhood |
| Reset | Click ⟳ button | Clears selection, runs `fitView()`, redraws |
| Zoom in/out | Click +/- buttons | Zooms from center of graph area |

---

### 7. Internationalization (i18n)

Language toggle synced with other dashboard pages via `localStorage('krx-dashboard-lang')`.

| Key | Korean | English |
|-----|--------|---------|
| title | 테마 네트워크 | Theme Network |
| tab.topics | 토픽 | Topics |
| tab.insights | 인사이트 | Insights |
| tab.search | 검색 | Search |
| sec.clusters | 클러스터 구조 | Cluster Structure |
| sec.connectors | 핵심 연결 테마 | Key Connector Themes |
| sec.gaps | 구조적 갭 | Structural Gaps |
| conn.desc | 클러스터 간 연결에 핵심적인 테마 | Themes bridging multiple clusters |
| gap.desc | 연결이 약한 클러스터 쌍 | Cluster pairs with weak connections |
| meta.info | 글자 크기 = 매개 중심성 · 엣지 색상 = 클러스터 | Text size = Betweenness Centrality · Edge color = Cluster |

---

## Sub-Agent: `infranodus-plot`

**File**: `~/.claude/agents/infranodus-plot.md`

A reusable Claude Code sub-agent that generates InfraNodus-style network visualizations from any matrix or edge list data.

### When It Activates

Proactively used when the user requests:
- Network graph / network visualization
- Force-directed graph
- InfraNodus plot
- Any visual representation of matrix/graph data as an interactive SVG

### Input Data Formats

| Format | Description | Example |
|--------|-------------|---------|
| CSV matrix | Square matrix with headers | `correlation_matrix.csv` |
| JSON matrix | `{source: {target: weight}}` | `spillover.json` |
| CSV edge list | `source,target,weight` columns | `edges.csv` |
| JSON edge list | `[{source, target, weight}]` | `graph.json` |

### Output Formats

- **React TSX**: Self-contained `.tsx` component with inline algorithms and SVG rendering
- **Standalone HTML**: Single `.html` file with embedded JS (zero build step)

### Reference Implementation

The sub-agent reads these canonical files before every generation:

- `WWAI-MACRO/WWAI-GNN/frontend/app/spillovers/graph-algorithms.ts` — Louvain, betweenness centrality
- `WWAI-MACRO/WWAI-GNN/frontend/app/spillovers/force-atlas2.ts` — ForceAtlas2 engine
- `WWAI-MACRO/WWAI-GNN/frontend/app/spillovers/NetworkGraph.tsx` — Full visualization component

### Execution Workflow

1. Parse arguments (`@path`, `--output`, `--highlight`, `--threshold`, etc.)
2. Read reference implementation files
3. Read and parse data source
4. Build symmetric adjacency with threshold filtering
5. Run Louvain community detection + betweenness centrality
6. Run ForceAtlas2 layout (300-600 iterations, 3-phase convergence)
7. Generate React TSX or standalone HTML
8. Write output file, verify (TypeScript check or tag validation)
9. Report graph statistics, community breakdown, top centrality nodes

### Visual Constants

```
Background:       #0a0a12
Community colors: ['#4ecdc4', '#ffe66d', '#ff6b6b', '#a29bfe', '#fd79a8']
Node dot:         3-9px radius (betweenness centrality)
Node glow:        Gaussian blur in community color
Label font:       11-28px (betweenness centrality)
Label color:      Community color at 70-100% opacity
Edge stroke:      Community color at 8-15% opacity
Edge width:       0.5-2px (edge weight)
```

---

## Skill: `/plot:infranodus`

**File**: `~/.claude/skills/plot-infranodus.md`

A user-invocable skill wrapping the `infranodus-plot` sub-agent.

### Command Syntax

```bash
/plot:infranodus @<data-file> [options]

Options:
  --output react|html     Output format (default: auto-detect)
  --highlight <nodes>     Comma-separated node codes to box-highlight
  --title <string>        Graph title
  --lang ko|en            Language (default: en)
  --communities <n>       Max community count hint (default: auto)
  --threshold <float>     Edge weight filter threshold (default: 0.005)
  --target <path>         Output file path (default: auto-generated)
```

### Examples

```bash
# Visualize a correlation matrix
/plot:infranodus @data/correlation_matrix.csv --highlight KOR --title "Economic Network"

# Generate React component from spillover data
/plot:infranodus @spillover.json --output react --highlight USA,CHN --lang ko

# Simple edge list visualization
/plot:infranodus @edges.csv --output html --title "Trade Network"

# Custom threshold for dense matrices
/plot:infranodus @dense_matrix.csv --threshold 0.1 --communities 4
```

### Output Report

After generation, the skill reports:
- Output file path and format
- Node/edge counts, community breakdown
- Top nodes by centrality
- Layout iteration count
- Verification result (TypeScript or HTML validation)

### Integration

| Property | Value |
|----------|-------|
| Persona Affinity | Frontend, Architect, Analyzer |
| MCP Servers | None required |
| Complexity | Moderate |
| Supervision | No |
| Generation Time | 10-30 seconds |
| Output Size | 15-50KB |
| Max Nodes | ~100 (efficient) |

---

## File Reference

| File | Path | Purpose |
|------|------|---------|
| Frontend | `dashboard/frontend/theme-network.html` | 864-line single-file SPA (HTML+CSS+JS) |
| Backend Router | `dashboard/backend/routers/network.py` | FastAPI router with co-occurrence endpoint |
| Backend Entry | `dashboard/backend/main.py` | Mounts `/theme-network.html` route |
| Theme Data | `data/network_theme_data.csv` | Naver theme membership data (2922 stocks) |
| Fiedler Data | `data/naver_themes_weekly_fiedler_2025.csv` | Weekly Fiedler eigenvalues (268 themes) |
| Sub-Agent | `~/.claude/agents/infranodus-plot.md` | Reusable InfraNodus graph generator agent |
| Skill | `~/.claude/skills/plot-infranodus.md` | `/plot:infranodus` user-invocable skill |

---

## Key Design Decisions

1. **Pre-computed layout**: FA2 runs synchronously (500 frames) before first render. Users see the final converged result immediately — no loading animation or jitter. This matches InfraNodus's behavior ("always give fittable size initially").

2. **Screen-space text**: Font sizes are fixed pixel values (9-36px) independent of zoom level. This prevents text from becoming invisible when zoomed out or enormous when zoomed in.

3. **Centroid-based gravity**: FA2 gravity pulls toward the centroid of all nodes (not screen center). This prevents layout drift when `fitView()` changes the camera transform.

4. **Canvas 2D (not SVG)**: Canvas handles 60 nodes + 451 edges + glow effects more efficiently than DOM-based SVG. HiDPI support via `devicePixelRatio` scaling.

5. **Sidebar analytics**: Inspired by InfraNodus's right panel (Topics, Gap Insights, Relations). Provides structural insights without requiring the user to visually parse the graph.

6. **Daily cache invalidation**: The co-occurrence network is cached server-side with daily TTL. New trading day data triggers fresh computation.

7. **Zero dependencies**: All algorithms (Louvain, Brandes, ForceAtlas2) are implemented inline in ~90 lines of JavaScript. No d3, sigma.js, or other graph libraries.
