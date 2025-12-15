import React from "react";
import styles from "./Spinner.module.css";

const Spinner: React.FC<{size?: number}> = ({ size = 24 }) => (
  <span
    className={styles.spinner}
    style={{ width: size, height: size }}
    aria-label="Loading"
    role="status"
  />
);

export default Spinner;
