# Shadcn React Hooks

*   React useBoolean Hook
*   React useClickAnyWhere Hook
*   React useCopyToClipboard Hook
*   React useCountdown Hook
*   React useCounter Hook
*   React useDarkMode Hook
*   React DebounceCallback Hook
*   React useDebounceValue Hook
*   React useDocumentTitle Hook
*   React useEventCallback Hook
*   React useEventListener Hook
*   React useHover Hook
*   React IntersectionObserver Hook
*   React useInterval Hook
*   React useIsClient Hook
*   React useIsMounted Hook
*   React useIsomorphicLayout Hook
*   React useLocalStorage Hook
*   React useMap Hook
*   React useMediaQuery Hook
*   React useMousePosition Hook
*   React useOnClickOutside Hook
*   React useReadLocalStorage Hook
*   React useResizeObserver Hook
*   React useScreen Hook
*   React useScript Hook
*   React useScrollLock Hook
*   React useSessionStorage Hook
*   React useStep Hook
*   React useTernaryDarkMode Hook
*   React useTimeout Hook
*   React useToggle Hook
*   React useUnmount Hook
*   React useWindowSize Hook

# Listing of all components

.
├── accordion.tsx                                  # Accordion component using Radix UI
├── alert-dialog.tsx                               # Modal alert dialog component using Radix UI
├── alert.tsx                                      # Alert message component with variants
├── aspect-ratio.tsx                               # Aspect ratio component using Radix UI
├── avatar.tsx                                     # User avatar component with image and fallback
├── badge.tsx                                      # Badge component for status or tags
├── banner.tsx                                     # Dismissible banner/alert component
├── breadcrumb.tsx                                 # Breadcrumb navigation component
├── button.tsx                                     # Button component with variants using CVA
├── card.tsx                                       # Card layout component (header, content, footer)
├── carousel.tsx                                   # Carousel/slider component using Embla Carousel
├── checkbox.tsx                                   # Checkbox input component using Radix UI
├── collapsible.tsx                                # Collapsible content section using Radix UI
├── command.tsx                                    # Command palette/combobox using cmdk
├── context-menu.tsx                               # Right-click context menu using Radix UI
├── data-table/                                    # Data table components
│   └── index.tsx                                  # Advanced data table with sorting and pagination
├── dialog.tsx                                     # Modal dialog component using Radix UI
├── dropdown-menu.tsx                              # Dropdown menu component using Radix UI
├── form.tsx                                       # Form wrapper using react-hook-form and Radix UI
├── foundation/                                    # Base building block components
│   ├── GlassPanel.tsx                             # Glassmorphism style panel component
│   ├── InlineTag.tsx                              # Inline status tag component
│   ├── KeyValueList.tsx                           # Key-value pair grid display component
│   ├── PasswordPolicyList.tsx                     # Password requirement list component
│   ├── SectionHeader.tsx                          # Section header with title and actions
│   ├── StatCard.tsx                               # Metric/statistic display card
│   └── index.ts                                   # Exports foundation components
├── hover-card.tsx                                 # Hover card component using Radix UI
├── input.tsx                                      # Text input field component
├── label.tsx                                      # Form label component using Radix UI
├── navigation-menu.tsx                            # Navigation menu component using Radix UI
├── pagination.tsx                                 # Pagination control component
├── popover.tsx                                    # Popover component using Radix UI
├── progress.tsx                                   # Progress bar component using Radix UI
├── radio-group.tsx                                # Radio button group using Radix UI
├── resizable.tsx                                  # Resizable panel layout using react-resizable-panels
├── scroll-area.tsx                                # Custom scrollable area using Radix UI
├── select.tsx                                     # Select dropdown component using Radix UI
├── separator.tsx                                  # Visual separator component using Radix UI
├── shadcn-io/                                     # Specialized UI and AI components
│   ├── ai/                                        # AI-specific interface components
│   │   ├── actions.tsx                            # Action buttons for AI interfaces
│   │   ├── branch.tsx                             # Conversation branching controls
│   │   ├── code-block.tsx                         # Code block with syntax highlighting
│   │   ├── conversation.tsx                       # Chat conversation container
│   │   ├── image.tsx                              # AI generated image renderer
│   │   ├── inline-citation.tsx                    # Inline citation and source components
│   │   ├── loader.tsx                             # SVG spinner/loader
│   │   ├── message.tsx                            # Chat message bubbles (user/assistant)
│   │   ├── prompt-input.tsx                       # Chat input area with attachments
│   │   ├── reasoning.tsx                          # Collapsible AI reasoning display
│   │   ├── response.tsx                           # Markdown renderer for AI responses
│   │   ├── source.tsx                             # Source reference list component
│   │   ├── suggestion.tsx                         # Prompt suggestion chips
│   │   ├── task.tsx                               # Task item display component
│   │   ├── tool.tsx                               # Tool execution display component
│   │   └── web-preview.tsx                        # Iframe-based web content preview
│   ├── animated-beam/                             # Connecting beam animation
│   │   └── index.tsx                              # Animated beam SVG component
│   ├── animated-testimonials/                     # Testimonial slider
│   │   └── index.tsx                              # Animated testimonial carousel
│   ├── animated-tooltip/                          # Avatar tooltips
│   │   └── index.tsx                              # Tooltip with hover animation
│   ├── avatar-group/                              # Grouped avatars
│   │   └── index.tsx                              # Stacked avatar display component
│   ├── code-block/                                # Enhanced code block
│   │   ├── index.tsx                              # Code block with file icons and themes
│   │   └── server.tsx                             # Server-side code highlighting
│   ├── copy-button/                               # Copy utility
│   │   └── index.tsx                              # Animated copy-to-clipboard button
│   ├── dropzone/                                  # File upload
│   │   └── index.tsx                              # File dropzone component
│   ├── magnetic/                                  # Motion effect
│   │   └── index.tsx                              # Magnetic hover effect wrapper
│   ├── marquee/                                   # Infinite scroll
│   │   └── index.tsx                              # Infinite scrolling marquee
│   ├── navbar-05/                                 # Navigation bar
│   │   └── index.tsx                              # Responsive navbar implementation
│   ├── spinner/                                   # Loading indicators
│   │   └── index.tsx                              # Multi-variant spinner component
│   ├── status/                                    # Status indicators
│   │   └── index.tsx                              # Status badge with dot indicator
│   └── video-player/                              # Media player
│       └── index.tsx                              # Video player using media-chrome
├── shape-landing-hero.tsx                         # Animated geometric hero section
├── sheet.tsx                                      # Side sheet/drawer component using Radix UI
├── skeleton.tsx                                   # Loading skeleton placeholder
├── sonner.tsx                                     # Toast provider wrapper for Sonner
├── states/                                        # UI state components
│   ├── EmptyState.tsx                             # Component for empty data states
│   ├── ErrorState.tsx                             # Component for error states
│   ├── SkeletonPanel.tsx                          # Loading skeleton panel state
│   └── index.ts                                   # Exports state components
├── switch.tsx                                     # Toggle switch component using Radix UI
├── table.tsx                                      # HTML table component
├── tabs.tsx                                       # Tabs component using Radix UI
├── textarea.tsx                                   # Textarea input component
├── theme-toggle.tsx                               # Dark mode toggle button
├── toggle.tsx                                     # Toggle button component using Radix UI
├── tooltip.tsx                                    # Tooltip component using Radix UI
└── use-toast.ts                                   # Hook for triggering toasts