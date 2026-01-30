# Fiedler Value Calculation Performance Analysis

## Current Implementation

### Scale
- **Themes**: 265 themes with ≥3 stocks
- **Average stocks per theme**: 27.1 stocks
- **Rolling window**: 20 days
- **Step size**: 5 days (75% overlap)
- **Data period**: 2025 YTD (~200+ trading days)

### Computational Complexity

**Per Theme Calculation:**
- Windows per theme: `(200 - 20) / 5 = ~36 windows`
- Total windows: `265 themes × 36 = ~9,540 Fiedler calculations`

**Per Window Operations:**
1. **Correlation Matrix**: O(n²) = O(27²) ≈ 729 operations
2. **Graph Building**: O(n²) ≈ 729 operations  
3. **Eigenvalue Calculation**: O(n³) ≈ 19,683 operations (using `np.linalg.eigvalsh`)
4. **Total per window**: ~21,000 operations

**Total Operations:**
- ~200 million operations per full run
- Estimated time: **15-30 minutes** (depending on CPU and I/O)

---

## Performance Bottlenecks

### 1. Full Eigenvalue Decomposition ⚠️
**Current**: Uses `np.linalg.eigvalsh(L)` - calculates ALL eigenvalues
- Complexity: O(n³)
- Only needs 2nd smallest eigenvalue

**Better**: Use sparse eigenvalue solver (already in some scripts)
```python
from scipy.sparse.linalg import eigsh
eigenvalues = eigsh(laplacian_sparse, k=2, which='SM', return_eigenvectors=False)
```
- Complexity: O(n²) for sparse matrices
- **Speedup: 5-10x**

### 2. No Incremental Updates ⚠️
**Current**: Recalculates all windows every time
- Each day adds 1 new window, but recalculates all 36

**Better**: Cache previous calculations
- Only calculate new window (last 20 days)
- **Speedup: 30-40x for daily updates**

### 3. Sequential Processing ⚠️
**Current**: Processes themes one by one
- 265 themes processed sequentially

**Better**: Parallel processing
- Use `multiprocessing` or `joblib`
- Process 4-8 themes simultaneously
- **Speedup: 4-8x**

### 4. Price Data Loading ⚠️
**Current**: Loads all price data every time
- ~2,300 stock CSV files read from disk

**Better**: 
- Cache loaded data in memory
- Use HDF5 or Parquet for faster I/O
- **Speedup: 2-3x**

---

## Optimization Strategy

### Phase 1: Quick Wins (1-2 hours implementation)
1. **Switch to sparse eigenvalue solver**
   - Replace `np.linalg.eigvalsh` with `eigsh` from scipy
   - **Expected speedup: 5-10x**

2. **Add incremental calculation**
   - Cache previous Fiedler values
   - Only calculate new window for latest date
   - **Expected speedup: 30-40x for daily runs**

### Phase 2: Medium Effort (4-6 hours)
3. **Parallel theme processing**
   - Use `multiprocessing.Pool` or `joblib.Parallel`
   - Process 4-8 themes in parallel
   - **Expected speedup: 4-8x**

4. **Optimize data loading**
   - Cache price data in memory
   - Use faster file format (HDF5/Parquet)
   - **Expected speedup: 2-3x**

### Phase 3: Advanced (1-2 days)
5. **Database caching**
   - Store Fiedler values in SQLite/PostgreSQL
   - Query only missing dates
   - **Expected speedup: 50-100x for daily updates**

6. **GPU acceleration** (if available)
   - Use CuPy for correlation/eigenvalue calculations
   - **Expected speedup: 10-50x**

---

## Estimated Performance After Optimization

### Current Performance
- **Full run**: 15-30 minutes
- **Daily update**: 15-30 minutes (recalculates everything)

### After Phase 1 Optimizations
- **Full run**: 2-5 minutes
- **Daily update**: **30-60 seconds** (incremental)

### After Phase 2 Optimizations
- **Full run**: 30-60 seconds
- **Daily update**: **10-20 seconds**

### After Phase 3 Optimizations
- **Full run**: 30-60 seconds
- **Daily update**: **1-5 seconds** (database query)

---

## Recommended Implementation Order

### For Daily Use (Priority 1)
1. ✅ **Incremental calculation** - Only calculate new date
2. ✅ **Sparse eigenvalue solver** - Faster per-calculation
3. ✅ **Result caching** - Store in JSON/CSV for quick lookup

### For Weekly Full Runs (Priority 2)
4. ✅ **Parallel processing** - Process themes in parallel
5. ✅ **Optimized data loading** - Cache price data

### For Production (Priority 3)
6. ✅ **Database storage** - SQLite for Fiedler values
7. ✅ **Incremental updates** - Only missing dates

---

## Code Changes Needed

### 1. Sparse Eigenvalue Solver
```python
# Current (slow)
L = nx.laplacian_matrix(G, weight='weight').toarray()
eigenvalues = np.linalg.eigvalsh(L)  # O(n³)

# Optimized (fast)
from scipy.sparse.linalg import eigsh
L_sparse = nx.laplacian_matrix(G, weight='weight')
eigenvalues = eigsh(L_sparse, k=2, which='SM', return_eigenvectors=False)  # O(n²)
```

### 2. Incremental Calculation
```python
# Load previous results
prev_file = DATA_DIR / f'theme_{theme}_timeseries.csv'
if prev_file.exists():
    prev_df = pd.read_csv(prev_file)
    last_date = prev_df['date'].max()
    # Only calculate windows after last_date
else:
    # Calculate all windows
```

### 3. Parallel Processing
```python
from joblib import Parallel, delayed

def process_theme(theme, tickers):
    return calculate_rolling_theme_fiedler(theme, tickers, data_dict)

results = Parallel(n_jobs=4)(
    delayed(process_theme)(theme, tickers) 
    for theme, tickers in theme_stocks.items()
)
```

---

## Conclusion

**Current**: Daily calculation takes **15-30 minutes** (recalculates everything)

**After Quick Wins**: Daily calculation takes **30-60 seconds** (incremental + sparse)

**Recommendation**: Implement Phase 1 optimizations for immediate 30-40x speedup on daily runs.

The calculation is computationally intensive but can be optimized significantly with incremental updates and sparse matrix operations.

