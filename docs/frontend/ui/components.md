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
├── auth/                        # Contains authentication-related form components.
│   ├── ForgotPasswordForm.tsx   # A form for users to request a password reset link.
│   ├── LoginForm.tsx            # A form for user authentication (email, password, tenant).
│   ├── LogoutButton.tsx         # A simple button component to handle user logout.
│   ├── RegisterForm.tsx         # A form for new user and organization registration.
│   ├── ResetPasswordForm.tsx    # A form for users to set a new password using a token.
│   └── SilentRefresh.tsx        # A component to handle silent session token refreshing.
└── ui/                          # Contains all UI components, including shadcn/ui and custom ones.
    ├── accordion.tsx            # A vertically stacked set of interactive headings that each reveal a section of content.
    ├── alert-dialog.tsx         # A modal dialog that interrupts the user with important content and requires a response.
    ├── alert.tsx                # Displays a callout for user attention.
    ├── aspect-ratio.tsx         # A container that maintains a specific aspect ratio.
    ├── avatar.tsx               # An image element with a fallback for representing a user.
    ├── badge.tsx                # Displays a small amount of information, such as a status.
    ├── breadcrumb.tsx           # Displays the path to the current resource.
    ├── button.tsx               # A standard button component.
    ├── card.tsx                 # A container for content with header, content, and footer sections.
    ├── carousel.tsx             # A carousel component for cycling through elements.
    ├── checkbox.tsx             # A control that allows the user to toggle between checked and not checked.
    ├── collapsible.tsx          # An interactive component which expands/collapses a content area.
    ├── command.tsx              # A command menu for search and navigation, like Spotlight.
    ├── context-menu.tsx         # Displays a menu to the user — such as a set of actions — when they right-click.
    ├── data-table/              # Reusable data table component.
    │   └── index.tsx            # A feature-rich data table with sorting, pagination, and state handling.
    ├── dialog.tsx               # A window overlaid on either the primary window or another dialog window.
    ├── dropdown-menu.tsx        # Displays a menu to the user — such as a set of actions — triggered by a button.
    ├── form.tsx                 # Components for building accessible forms with react-hook-form.
    ├── foundation/              # Contains custom, foundational UI components for the application's design system.
    │   ├── GlassPanel.tsx       # A panel component with a frosted glass visual effect.
    │   ├── InlineTag.tsx        # A small, styled tag for displaying status or category.
    │   ├── KeyValueList.tsx     # A component for displaying lists of key-value pairs.
    │   ├── SectionHeader.tsx    # A reusable header component for sections of the UI.
    │   ├── StatCard.tsx         # A card for displaying a single statistic with a label and optional trend.
    │   └── index.ts             # Exports all components from the foundation directory.
    ├── hover-card.tsx           # A pop-up that displays information on hover.
    ├── input.tsx                # A standard text input field.
    ├── label.tsx                # Renders an accessible label associated with a form control.
    ├── navigation-menu.tsx      # A collection of links for navigating a website.
    ├── pagination.tsx           # Components for navigating between pages of content.
    ├── popover.tsx              # Displays rich content in a portal, triggered by a button.
    ├── progress.tsx             # Displays an indicator showing the completion progress of a task.
    ├── radio-group.tsx          # A set of checkable buttons, where only one can be selected at a time.
    ├── resizable.tsx            # Components for creating resizable panel layouts.
    ├── scroll-area.tsx          # A scrollable area with custom scrollbars.
    ├── select.tsx               # A control that allows a user to select one option from a list.
    ├── separator.tsx            # A visual separator between content.
    ├── shadcn-io/               # Pre-built, complex components from the shadcn.io/ui library.
    │   ├── ai/                  # Components specifically designed for building AI chat interfaces.
    │   │   ├── actions.tsx      # Container and button components for actions on an AI message.
    │   │   ├── branch.tsx       # Component to manage and navigate between different AI response branches.
    │   │   ├── code-block.tsx   # A client-side syntax-highlighted code block with a copy button.
    │   │   ├── conversation.tsx # A scrollable container for chat messages with stick-to-bottom behavior.
    │   │   ├── image.tsx        # Component to render AI-generated images from base64 strings.
    │   │   ├── inline-citation.tsx # Components for displaying inline source citations with a hover card.
    │   │   ├── loader.tsx       # An animated loading spinner icon.
    │   │   ├── message.tsx      # Components for displaying a single chat message (user or assistant).
    │   │   ├── prompt-input.tsx # An advanced text area for composing and submitting prompts.
    │   │   ├── reasoning.tsx    # A collapsible section to show the AI's step-by-step reasoning.
    │   │   ├── response.tsx     # A component for rendering markdown content from AI responses securely.
    │   │   ├── source.tsx       # A collapsible section to display sources used by the AI.
    │   │   ├── suggestion.tsx   # A scrollable list of suggested prompts for the user.
    │   │   ├── task.tsx         # A collapsible section to display tasks performed by the AI.
    │   │   ├── tool.tsx         # A collapsible section to show the details of a tool used by the AI.
    │   │   └── web-preview.tsx  # An iframe-based component to preview web pages.
    │   ├── animated-beam/       # Directory for the animated beam component.
    │   │   └── index.tsx        # A component that creates an animated beam between two elements.
    │   ├── animated-testimonials/ # Directory for animated testimonials component.
    │   │   └── index.tsx        # A component for displaying testimonials with smooth animations.
    │   ├── animated-tooltip/    # Directory for animated tooltip component.
    │   │   └── index.tsx        # An animated tooltip for displaying user information on hover.
    │   ├── avatar-group/        # Directory for avatar group component.
    │   │   └── index.tsx        # A component for displaying a group of overlapping avatars.
    │   ├── code-block/          # Directory for a feature-rich code block component.
    │   │   ├── index.tsx        # A client-side code block component with file tabs and language icons.
    │   │   └── server.tsx       # A server-side rendered code block component using Shiki.
    │   ├── copy-button/         # Directory for copy button component.
    │   │   └── index.tsx        # A button to copy text to the clipboard with visual feedback.
    │   ├── dropzone/            # Directory for file dropzone component.
    │   │   └── index.tsx        # A drag-and-drop file upload component.
    │   ├── magnetic/            # Directory for a magnetic effect component.
    │   │   └── index.tsx        # A wrapper that applies a magnetic attraction effect to its child element.
    │   ├── marquee/             # Directory for a marquee/scrolling text component.
    │   │   └── index.tsx        # A component for creating a continuous scrolling effect.
    │   ├── navbar-05/           # Directory for a pre-built navbar component.
    │   │   └── index.tsx        # A complete, responsive navigation bar component.
    │   ├── spinner/             # Directory for spinner components.
    │   │   └── index.tsx        # A collection of various animated loading spinners.
    │   ├── status/              # Directory for a status indicator component.
    │   │   └── index.tsx        # A badge component to indicate status like online, offline, etc.
    │   └── video-player/        # Directory for a video player component.
    │       └── index.tsx        # A customizable video player built on top of Media Chrome.
    ├── shape-landing-hero.tsx   # A hero section component with animated geometric shapes for a landing page.
    ├── sheet.tsx                # A slide-out panel that appears from the edge of the screen.
    ├── skeleton.tsx             # A component to display a placeholder preview of content before it loads.
    ├── sonner.tsx               # A toast notification component for displaying brief messages.
    ├── states/                  # Contains components for displaying various UI states.
    │   ├── EmptyState.tsx       # A component to show when no data is available.
    │   ├── ErrorState.tsx       # A component to show when an error has occurred.
    │   ├── SkeletonPanel.tsx    # A panel filled with skeleton loaders for loading states.
    │   └── index.ts             # Exports all state components.
    ├── switch.tsx               # A two-state toggle switch.
    ├── table.tsx                # Components for displaying tabular data.
    ├── tabs.tsx                 # A set of layered sections of content, known as tab panels, that are displayed one at a time.
    ├── textarea.tsx             # A multiline text input field.
    ├── theme-toggle.tsx         # A button for switching between light and dark color themes.
    ├── toggle.tsx               # A two-state button that can be either on or off.
    ├── tooltip.tsx              # A popup that displays information related to an element when it's hovered.
    └── use-toast.ts             # A custom hook for triggering toast notifications using Sonner.