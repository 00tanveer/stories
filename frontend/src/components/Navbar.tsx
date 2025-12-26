"use client";

import React from "react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import navStyles from "./Navbar.module.css";

const Navbar: React.FC = () => {
    const pathname = usePathname();

    return (
        <nav className={navStyles.navbar}>
            <Link href="/" className={navStyles.logoLink}>
                <img 
                    src="/logo.png"
                    alt="Stories Logo"
                    className={navStyles.logo}
                />
            </Link>
            
            <div className={navStyles.navLinks}>
                <Link 
                    href="/search" 
                    className={`${navStyles.navLink} ${pathname === '/search' ? navStyles.active : ''}`}
                >
                    Search
                </Link>
                <Link 
                    href="/explore" 
                    className={`${navStyles.navLink} ${pathname === '/explore' ? navStyles.active : ''}`}
                >
                    Explore
                </Link>
            </div>
        </nav>
    );
}

export default Navbar;