import * as React from "react"
import styles from "./Input.module.css"

export interface InputProps extends React.InputHTMLAttributes<HTMLInputElement> {}

const Input = React.forwardRef<HTMLInputElement, InputProps>(
  ({ className = "", type = "text", ...props }, ref) => {
    return (
      <input
        type={type}
        className={[styles.input, className].filter(Boolean).join(" ")}
        ref={ref}
        {...props}
      />
    )
  }
)
Input.displayName = "Input"
export { Input }