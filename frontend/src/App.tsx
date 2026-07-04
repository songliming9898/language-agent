import { BrowserRouter, Routes, Route } from "react-router-dom";
import Home from "./pages/Home";
import CourseList from "./pages/CourseList";
import UnitList from "./pages/UnitList";
import CoursePractice from "./pages/CoursePractice";
import FreeTalk from "./pages/FreeTalk";
import Report from "./pages/Report";

export default function App() {
  return (
    <BrowserRouter>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/courses" element={<CourseList />} />
        <Route path="/courses/:courseId/units" element={<UnitList />} />
        <Route path="/practice/:unitId" element={<CoursePractice />} />
        <Route path="/free-talk" element={<FreeTalk />} />
        <Route path="/report" element={<Report />} />
      </Routes>
    </BrowserRouter>
  );
}
