import { BrowserRouter, Routes, Route } from 'react-router-dom'
import { Dashboard } from '@/pages/Dashboard'
import { NewTrip } from '@/pages/NewTrip'
import { TripDetail } from '@/pages/TripDetail'
import { Templates } from '@/pages/Templates'
import { TemplateDetail } from '@/pages/TemplateDetail'

export default function App() {
  return (
    <BrowserRouter>
      <div className="min-h-screen bg-gray-50">
        <Routes>
          <Route path="/" element={<Dashboard />} />
          <Route path="/trips/new" element={<NewTrip />} />
          <Route path="/trips/:id" element={<TripDetail />} />
          <Route path="/templates" element={<Templates />} />
          <Route path="/templates/:id" element={<TemplateDetail />} />
        </Routes>
      </div>
    </BrowserRouter>
  )
}
