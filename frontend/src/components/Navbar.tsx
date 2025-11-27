import React from "react";
import { Button } from "./ui/button";
import navStyles from "./Navbar.module.css";
import styles from "./ui/Button.module.css"


// import ThemeToggle from "./ThemeToggle";

const Navbar: React.FC = () => {
    return (
        <nav className={navStyles.navbar}>
            <Button className={styles.buttonSecondary}>
                Ask questions
            </Button>
            <Button className={styles.buttonSecondary}>
                How to use Stories?
            </Button>
            {/* <ThemeToggle /> */}
        </nav>
    );
}

export default Navbar;