import React from "react";
import navStyles from "./Navbar.module.css";


// import ThemeToggle from "./ThemeToggle";

const Navbar: React.FC = () => {
    return (
        <nav className={navStyles.navbar}>
            <img 
                src="/logo.png"
                alt="Stories Logo"
                className={navStyles.logo}
            />
            <h1>Stories</h1>
            {/* <ThemeToggle /> */}
            {/* <Button className={navStyles.howToBtn}>
                ?
            </Button> */}
        </nav>
    );
}

export default Navbar;