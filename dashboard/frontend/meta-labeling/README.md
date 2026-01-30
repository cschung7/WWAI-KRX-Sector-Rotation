# Meta-Labeling Dashboard

Financial market dashboard for meta-labeling signal filtering and performance monitoring.

## Features

- **Real-Time Performance Metrics**: Win rate, returns, Sharpe ratio
- **Signal Filtering**: Filter signals using trained meta-labeler
- **Performance Comparison**: Baseline vs filtered metrics
- **Model Status**: View current model information
- **Historical Tracking**: Performance over time

## Setup

### 1. Install Dependencies

```bash
npm install
```

### 2. Configure API URL

Create `.env` file:

```
REACT_APP_API_URL=http://localhost:8000
```

### 3. Start Development Server

```bash
npm start
```

Access at: `http://localhost:3000`

## Build for Production

```bash
npm run build
```

## Technology Stack

- **React 18**: UI framework
- **Tailwind CSS**: Styling
- **Recharts**: Data visualization
- **Axios**: HTTP client
- **Heroicons**: Icons

## API Endpoints Used

- `GET /api/meta-labeling/status` - Model status
- `GET /api/meta-labeling/performance` - Performance metrics
- `POST /api/meta-labeling/filter` - Filter signals
- `GET /api/meta-labeling/history` - Performance history

