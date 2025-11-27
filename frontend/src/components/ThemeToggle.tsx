
import { useTheme } from "../hooks/useTheme";
import buttonStyles from "./ui/Button.module.css";

export default function ThemeToggle() {
  const { theme, toggleTheme } = useTheme();
  return (
    <button
      type="button"
      onClick={toggleTheme}
      aria-label="Toggle theme"
      className={buttonStyles.button}
      style={{ marginLeft: "1rem" }}
    >
      {theme === "dark" ? "🌙 Dark" : "☀️ Light"}
    </button>
  );
}
