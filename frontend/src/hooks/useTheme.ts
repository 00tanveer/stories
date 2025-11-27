import { useCallback } from "react";

export function useTheme() {
  // Get current theme from <html data-theme="...">
  const getTheme = () => {
    if (typeof document === "undefined") return "light";
    return document.documentElement.getAttribute("data-theme") || "light";
  };

  // Set theme on <html>
  const setTheme = useCallback((theme: "light" | "dark") => {
    document.documentElement.setAttribute("data-theme", theme);
  }, []);

  // Toggle theme
  const toggleTheme = useCallback(() => {
    setTheme(getTheme() === "dark" ? "light" : "dark");
  }, [setTheme]);

  return { theme: getTheme(), setTheme, toggleTheme };
}
