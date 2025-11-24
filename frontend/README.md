# Altur - Call Transcription Frontend

Frontend application for Altur Call Transcription Service built with React, Material UI, and Tailwind CSS.

## Features

- 📞 View all call records
- 📤 Upload and process audio files
- 🔍 Filter calls by tags
- 📊 Analytics dashboard
- 📄 View detailed call information
- 💾 Export calls as JSON
- 🗑️ Delete calls
- 📱 Responsive design

## Prerequisites

- Node.js 18+
- npm or yarn

## Installation

1. **Install dependencies:**
```bash
npm install
```

2. **Set up environment variables:**
Create a `.env` file in the root directory:
```env
VITE_API_URL=http://localhost:5000
```

## Running

### Development Mode
```bash
npm run dev
```

The application will start on `http://localhost:5173`

### Production Build
```bash
npm run build
```

### Preview Production Build
```bash
npm run preview
```

## Project Structure

```
frontend/
├── src/
│   ├── components/
│   │   └── Layout.jsx          # Main layout with navigation
│   ├── pages/
│   │   ├── CallsList.jsx       # List of all calls
│   │   ├── CallDetail.jsx      # Detailed view of a call
│   │   └── Analytics.jsx       # Analytics dashboard
│   ├── services/
│   │   └── api.js              # API client
│   ├── theme.js                # Material UI theme
│   ├── App.jsx                 # Main app component
│   └── main.jsx                # Entry point
├── package.json
└── vite.config.js
```

## API Integration

The frontend consumes the following endpoints:

- `POST /api/calls` - Upload and process a call
- `GET /api/calls` - Get all calls (with optional tag filter)
- `GET /api/calls/:id` - Get a single call
- `GET /api/calls/:id/export` - Export call as JSON
- `DELETE /api/calls/:id` - Delete a call
- `GET /api/calls/analytics` - Get analytics

## Styling

- **Material UI**: Component library and theme
- **Tailwind CSS**: Utility-first CSS framework
- **Color Scheme**: White and blue (Altur branding)
  - Primary Blue: #1976D2
  - Light Blue: #42A5F5
  - Dark Blue: #1565C0

## Browser Support

- Chrome (latest)
- Firefox (latest)
- Safari (latest)
- Edge (latest)
