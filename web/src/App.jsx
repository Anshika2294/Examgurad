import { BrowserRouter, Routes, Route, Navigate } from "react-router-dom";
import StudentLogin from "./pages/student/Login";
import StudentRegister from "./pages/student/Register";
import AdminLogin from "./pages/admin/Login";

function StudentDashboard() {
  return <h2 style={{ textAlign: "center", marginTop: 60 }}>Student dashboard (coming soon)</h2>;
}

function AdminDashboard() {
  return <h2 style={{ textAlign: "center", marginTop: 60 }}>Admin dashboard (coming soon)</h2>;
}

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Navigate to="/student/login" />} />
        <Route path="/student/login" element={<StudentLogin />} />
        <Route path="/student/register" element={<StudentRegister />} />
        <Route path="/student/dashboard" element={<StudentDashboard />} />
        <Route path="/admin/login" element={<AdminLogin />} />
        <Route path="/admin/dashboard" element={<AdminDashboard />} />
      </Routes>
    </BrowserRouter>
  );
}