import type { ReactNode } from "react"
import { LoaderCircle } from "lucide-react"

import { cn } from "@/lib/utils"

export type NodeStatus = "loading" | "success" | "error" | "initial"

export type NodeStatusVariant = "overlay" | "border"

export type NodeStatusIndicatorProps = {
  status?: NodeStatus
  variant?: NodeStatusVariant
  children: ReactNode
}

export const SpinnerLoadingIndicator = ({
  children,
}: {
  children: ReactNode
}) => {
  return (
    <div className="relative">
      <StatusBorder className="border-primary/40">{children}</StatusBorder>

      <div className="bg-background/50 absolute inset-0 z-50 rounded-[9px] backdrop-blur-sm" />
      <div className="absolute inset-0 z-50">
        <span className="absolute top-[calc(50%-1.25rem)] left-[calc(50%-1.25rem)] inline-block h-10 w-10 animate-ping rounded-full bg-primary/20" />

        <LoaderCircle className="absolute top-[calc(50%-0.75rem)] left-[calc(50%-0.75rem)] size-6 animate-spin text-primary" />
      </div>
    </div>
  )
}

export const BorderLoadingIndicator = ({
  children,
}: {
  children: ReactNode
}) => {
  return (
    <>
      <div className="absolute -top-px -left-px h-[calc(100%+2px)] w-[calc(100%+2px)]">
        <div className="absolute inset-0 overflow-hidden rounded-[9px]">
          <div className="absolute left-1/2 top-1/2 w-[140%] -translate-x-1/2 -translate-y-1/2 aspect-square">
            <div className="h-full w-full animate-spin rounded-full bg-[conic-gradient(from_0deg_at_50%_50%,hsl(var(--primary))_0deg,transparent_360deg)]" />
          </div>
        </div>
      </div>
      {children}
    </>
  )
}

const StatusBorder = ({
  children,
  className,
}: {
  children: ReactNode
  className?: string
}) => {
  return (
    <>
      <div
        className={cn(
          "absolute -top-px -left-px h-[calc(100%+2px)] w-[calc(100%+2px)] rounded-[9px] border-2",
          className
        )}
      />
      {children}
    </>
  )
}

export const NodeStatusIndicator = ({
  status,
  variant = "border",
  children,
}: NodeStatusIndicatorProps) => {
  switch (status) {
    case "loading":
      switch (variant) {
        case "overlay":
          return <SpinnerLoadingIndicator>{children}</SpinnerLoadingIndicator>
        case "border":
          return <BorderLoadingIndicator>{children}</BorderLoadingIndicator>
        default:
          return <>{children}</>
      }
    case "success":
      return (
        <StatusBorder className="border-emerald-600">{children}</StatusBorder>
      )
    case "error":
      return <StatusBorder className="border-red-400">{children}</StatusBorder>
    default:
      return <>{children}</>
  }
}
