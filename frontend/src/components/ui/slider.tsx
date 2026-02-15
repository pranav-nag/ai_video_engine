
import * as React from "react"
import * as SliderPrimitive from "@radix-ui/react-slider"
import { cn } from "@/lib/utils"

const Slider = React.forwardRef<
  React.ComponentRef<typeof SliderPrimitive.Root>,
  React.ComponentPropsWithoutRef<typeof SliderPrimitive.Root>
>(({ className, ...props }, ref) => (
  <SliderPrimitive.Root
    ref={ref}
    className={cn(
      "relative flex w-full touch-none select-none items-center",
      className
    )}
    {...props}
  >
    <SliderPrimitive.Track className="relative h-1.5 w-full grow overflow-hidden rounded-full bg-secondary/50">
      <SliderPrimitive.Range className="absolute h-full bg-primary" />
    </SliderPrimitive.Track>
    <SliderPrimitive.Thumb className="block h-4 w-4 rounded-full border border-primary/50 bg-background ring-offset-background disabled:pointer-events-none disabled:opacity-50 shadow-[0_0_10px_rgba(124,58,237,0.5)] hover:bg-primary/20 hover:scale-110 transition-transform" />
    {/* Support for Range slider (2 thumbs) */}
    {props.defaultValue && props.defaultValue.length > 1 && (
        <SliderPrimitive.Thumb className="block h-4 w-4 rounded-full border border-primary/50 bg-background ring-offset-background disabled:pointer-events-none disabled:opacity-50 shadow-[0_0_10px_rgba(124,58,237,0.5)] hover:bg-primary/20 hover:scale-110 transition-transform" />
    )}
  </SliderPrimitive.Root>
))
Slider.displayName = SliderPrimitive.Root.displayName

export { Slider }
