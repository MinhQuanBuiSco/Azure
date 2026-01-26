import { type HTMLAttributes } from 'react'
import { cva, type VariantProps } from 'class-variance-authority'
import { clsx } from 'clsx'
import { twMerge } from 'tailwind-merge'

function cn(...inputs: (string | undefined | null | boolean)[]) {
  return twMerge(clsx(inputs))
}

const badgeVariants = cva(
  'inline-flex items-center rounded-full px-2.5 py-0.5 text-xs font-medium transition-colors',
  {
    variants: {
      variant: {
        default:
          'bg-primary/20 text-primary border border-primary/30',
        secondary:
          'bg-secondary/50 text-secondary-foreground border border-secondary/30',
        success:
          'bg-green-500/20 text-green-400 border border-green-500/30',
        warning:
          'bg-yellow-500/20 text-yellow-400 border border-yellow-500/30',
        error:
          'bg-red-500/20 text-red-400 border border-red-500/30',
        outline:
          'border border-white/20 text-foreground',
        glass:
          'glass text-foreground',
      },
    },
    defaultVariants: {
      variant: 'default',
    },
  }
)

export interface BadgeProps
  extends HTMLAttributes<HTMLDivElement>,
    VariantProps<typeof badgeVariants> {}

function Badge({ className, variant, ...props }: BadgeProps) {
  return (
    <div className={cn(badgeVariants({ variant }), className)} {...props} />
  )
}

export { Badge, badgeVariants }
