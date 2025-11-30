import * as React from "react"
import styles from "./Button.module.css"

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "destructive" | "outline" | "ghost" | "link"
  size?: "sm" | "default" | "lg" | "icon"
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "default", className = "", children, ...props }, ref) => {
    const variantClass = (() => {
      switch (variant) {
        case "secondary":
          return styles.buttonSecondary
        case "destructive":
          return styles.buttonDestructive
        case "outline":
          return styles.buttonOutline
        case "ghost":
          return styles.buttonGhost
        case "link":
          return styles.buttonLink
        default:
          return styles.buttonPrimary
      }
    })()

    const sizeClass = (() => {
      switch (size) {
        case "sm":
          return styles.sizeSm
        case "lg":
          return styles.sizeLg
        case "icon":
          return styles.sizeIcon
        default:
          return styles.sizeDefault
      }
    })()

    const classNames = [styles.button, variantClass, sizeClass, className].filter(Boolean).join(" ")

    return (
      <button className={classNames} ref={ref} {...props}>
        {children}
      </button>
    )
  }
)

Button.displayName = "Button"

export { Button }