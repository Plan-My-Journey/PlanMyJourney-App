import { Navigate, Route, Routes } from "react-router-dom";

import Layout from "./components/Layout";
import ProtectedRoute from "./components/ProtectedRoute";
import AITravelAssistant from "./pages/AITravelAssistant";
import CreateTrip from "./pages/CreateTrip";
import Dashboard from "./pages/Dashboard";
import DestinationComparison from "./pages/DestinationComparison";
import ExpenseTracker from "./pages/ExpenseTracker";
import Login from "./pages/Login";
import CognitoCallback from "./pages/CognitoCallback";
import PackingAssistant from "./pages/PackingAssistant";
import Register from "./pages/Register";
import TripHistory from "./pages/TripHistory";
import UserProfile from "./pages/UserProfile";

export default function App() {
  return (
    <Routes>
      <Route path="/login" element={<Login />} />
      <Route path="/register" element={<Register />} />
      <Route path="/callback" element={<CognitoCallback />} />
      <Route element={<ProtectedRoute />}>
        <Route element={<Layout />}>
          <Route index element={<Dashboard />} />
          <Route path="create-trip" element={<CreateTrip />} />
          <Route path="history" element={<TripHistory />} />
          <Route path="expenses" element={<ExpenseTracker />} />
          <Route path="assistant" element={<AITravelAssistant />} />
          <Route path="compare" element={<DestinationComparison />} />
          <Route path="packing" element={<PackingAssistant />} />
          <Route path="profile" element={<UserProfile />} />
        </Route>
      </Route>
      <Route path="*" element={<Navigate to="/" replace />} />
    </Routes>
  );
}
