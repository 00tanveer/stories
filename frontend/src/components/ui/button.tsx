import * as React from "react"
import styles from "./Button.module.css"
import { Slot } from "@radix-ui/react-slot"

export interface ButtonProps extends React.ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: "primary" | "secondary" | "destructive" | "outline" | "ghost" | "link"
  size?: "sm" | "default" | "lg" | "icon"
  asChild?: boolean
}

const Button = React.forwardRef<HTMLButtonElement, ButtonProps>(
  ({ variant = "primary", size = "default", asChild = false, className = "", children, ...props }, ref) => {
    const Comp: any = asChild ? Slot : "button"

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
      <Comp className={classNames} ref={ref} {...props}>
        {children}
      </Comp>
    )
  }
)

Button.displayName = "Button"

export { Button }