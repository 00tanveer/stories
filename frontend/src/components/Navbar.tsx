import React from "react";
import { Button } from "./ui/button";
import navStyles from "./Navbar.module.css";


// import ThemeToggle from "./ThemeToggle";

const Navbar: React.FC = () => {
    return (
        <nav className={navStyles.navbar}>
            <h1>Stories</h1>
            {/* <ThemeToggle /> */}
            {/* <Button className={navStyles.howToBtn}>
                ?
            </Button> */}
        </nav>
    );
}

export default Navbar;