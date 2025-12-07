# Manufacturing AI Assistant - Web Interface

Modern chat interface for interacting with multi-agent manufacturing assistants.

## Quick Start

### 1. Install Dependencies

```bash
cd frontend
npm install
```

### 2. Configure API Endpoint

The frontend connects to the backend at `http://localhost:8000` by default.

To change this, edit `src/api.js` and update the `API_BASE` constant.

### 3. Run Development Server

```bash
npm run dev
```

Visit http://localhost:5173

## Building for Production

```bash
npm run build
```

This creates an optimized production build in the `dist/` directory.

## Features

- ✅ Machine selector dropdown
- ✅ Real-time chat interface
- ✅ Typing indicators during LLM processing
- ✅ Message metadata (agents used, execution time)
- ✅ Clear conversation button
- ✅ Responsive design (mobile-friendly)
- ✅ Modern, professional UI with animations

## Project Structure

```
frontend/
├── src/
│   ├── App.jsx          # Main application component
│   ├── App.css          # Styling
│   ├── api.js           # API client
│   └── main.jsx         # Entry point
├── package.json
└── vite.config.js
```

## Development

### Adding New Features

Edit `src/App.jsx` to add new components or functionality.

### Styling

All styles are in `src/App.css`. Uses CSS variables for easy theming.

### API Integration

The `src/api.js` file handles all backend communication. Add new API calls here.

## Deployment

For production deployment:

1. Build the app: `npm run build`
2. Serve the `dist/` directory with any static file server
3. Or use Docker (see root docker-compose.yml)

## Troubleshooting

### Backend Connection Failed

Make sure the backend is running on `http://localhost:8000`:

```bash
cd ../backend
uvicorn app.main:app --reload
```

### CORS Errors

The backend is configured to allow all origins in development. For production, update the CORS settings in `backend/app/main.py`.

### No Machines Showing

Check that machine config files exist in `backend/configs/`.
