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

# Shadcn React Components Installed

.
├── auth/                        # Contains authentication-related components.
│   ├── LoginForm.tsx            # A form component for user login.
│   ├── LogoutButton.tsx         # A button component to log the user out.
│   └── SilentRefresh.tsx        # A component to handle silent session token refreshing.
└── ui/                          # A collection of reusable UI components.
    ├── accordion.tsx            # A vertically stacked set of interactive headings that each reveal a section of content.
    ├── alert-dialog.tsx         # A modal dialog that interrupts the user with important content and requires a response.
    ├── alert.tsx                # A component that displays a short, important message.
    ├── aspect-ratio.tsx         # A container that maintains a specific aspect ratio.
    ├── avatar.tsx               # An image element with a fallback for user profiles.
    ├── badge.tsx                # A component to display small pieces of information, such as tags or statuses.
    ├── breadcrumb.tsx           # A navigation aid that shows the user's location in a site or app.
    ├── button.tsx               # A customizable button component with different variants.
    ├── card.tsx                 # A container for grouping related content and actions.
    ├── carousel.tsx             # A slideshow component for cycling through elements.
    ├── checkbox.tsx             # A control that allows the user to select one or more options from a set.
    ├── collapsible.tsx          # A component that can be expanded or collapsed to show or hide content.
    ├── command.tsx              # A command menu component for search and actions.
    ├── context-menu.tsx         # A menu that appears upon right-clicking or long-pressing an element.
    ├── dialog.tsx               # A window overlaid on either the primary window or another dialog window.
    ├── dropdown-menu.tsx        # A menu that appears when a user interacts with a button or other control.
    ├── form.tsx                 # Components and hooks for building type-safe forms with react-hook-form.
    ├── foundation/              # Foundational, custom-styled UI components.
    │   ├── GlassPanel.tsx       # A panel component with a glassmorphism visual effect.
    │   ├── InlineTag.tsx        # A styled tag for inline display with different tones.
    │   ├── KeyValueList.tsx     # A component for displaying lists of key-value pairs.
    │   ├── SectionHeader.tsx    # A standardized header for content sections with title, description, and actions.
    │   ├── StatCard.tsx         # A card component for displaying a single statistic with an optional trend.
    │   └── index.ts             # Exports all foundation components.
    ├── hover-card.tsx           # A pop-up card that appears when a user hovers over an element.
    ├── input.tsx                # A basic text input field component.
    ├── label.tsx                # A component for labeling form elements.
    ├── navigation-menu.tsx      # A navigation menu for website or app links.
    ├── pagination.tsx           # A component for navigating between pages of content.
    ├── popover.tsx              # A pop-up that displays content in relation to a trigger element.
    ├── progress.tsx             # A component to display the progress of a task.
    ├── radio-group.tsx          # A set of checkable buttons, known as radio buttons, where only one can be selected at a time.
    ├── resizable.tsx            # Components for creating resizable panel layouts.
    ├── scroll-area.tsx          # A scrollable view with a custom scrollbar.
    ├── select.tsx               # A control that allows users to choose one option from a list.
    ├── separator.tsx            # A component to visually separate content.
    ├── shadcn-io/               # UI components sourced from or inspired by shadcn.io/ui.
    │   ├── ai/                  # Components specifically for building AI and chat interfaces.
    │   │   ├── actions.tsx      # UI components for actions related to an AI message (e.g., copy, regenerate).
    │   │   ├── branch.tsx       # Components for managing and navigating between multiple AI response branches.
    │   │   ├── code-block.tsx   # A syntax-highlighted code block with a copy button.
    │   │   ├── conversation.tsx # A scrollable container for chat messages with a scroll-to-bottom feature.
    │   │   ├── image.tsx        # Renders an AI-generated image from base64 data.
    │   │   ├── inline-citation.tsx # Components for displaying inline citations with hover-able source details.
    │   │   ├── loader.tsx       # An animated loading spinner component.
    │   │   ├── message.tsx      # Components for styling user and assistant chat messages, including avatars.
    │   │   ├── prompt-input.tsx # A rich text input for user prompts with submit and model selection capabilities.
    │   │   ├── reasoning.tsx    # A collapsible component to display the AI's "thought process".
    │   │   ├── response.tsx     # A component for rendering markdown content, often from an AI response.
    │   │   ├── source.tsx       # Components for displaying a list of sources used by an AI.
    │   │   ├── suggestion.tsx   # A horizontal list of suggested prompts or actions for the user.
    │   │   ├── task.tsx         # A collapsible component to display a task the AI is performing.
    │   │   ├── tool.tsx         # Components to display the status, input, and output of a tool used by an AI.
    │   │   └── web-preview.tsx  # A component to render a web page preview in an iframe with a console.
    │   ├── animated-beam/       # Contains the AnimatedBeam component.
    │   │   └── index.tsx        # A component to draw an animated beam between two elements.
    │   ├── animated-testimonials/ # Contains the AnimatedTestimonials component.
    │   │   └── index.tsx        # A component to display testimonials with smooth animations.
    │   ├── animated-tooltip/    # Contains the AnimatedTooltip component.
    │   │   └── index.tsx        # A tooltip that animates and follows the cursor when hovering over an element.
    │   ├── avatar-group/        # Contains the AvatarGroup component.
    │   │   └── index.tsx        # A component to display a group of overlapping avatars with tooltips.
    │   ├── code-block/          # A feature-rich code block component.
    │   │   ├── index.tsx        # Client-side component for code blocks with file tabs and dynamic highlighting.
    │   │   └── server.tsx       # Server-side component for Shiki-based syntax highlighting.
    │   ├── copy-button/         # Contains the CopyButton component.
    │   │   └── index.tsx        # A standalone animated button for copying text to the clipboard.
    │   ├── dropzone/            # Contains the Dropzone component.
    │   │   └── index.tsx        # A component for file uploads via drag-and-drop or clicking.
    │   ├── magnetic/            # Contains the Magnetic component.
    │   │   └── index.tsx        # A wrapper component that makes its child magnetically follow the cursor.
    │   ├── marquee/             # Contains the Marquee component.
    │   │   └── index.tsx        # A component that creates a scrolling marquee effect for its content.
    │   ├── navbar-05/           # Contains a specific style of Navbar component.
    │   │   └── index.tsx        # A responsive navbar component with logo, navigation, and user menus.
    │   ├── spinner/             # Contains various spinner components.
    │   │   └── index.tsx        # A collection of different animated loading spinners.
    │   ├── status/              # Contains the Status component.
    │   │   └── index.tsx        # A component to display a status (e.g., online, offline) with an indicator dot and label.
    │   └── video-player/        # Contains the VideoPlayer component.
    │       └── index.tsx        # A video player component with standard controls, built on media-chrome.
    ├── shape-landing-hero.tsx   # A hero section component with animated geometric background shapes.
    ├── sheet.tsx                # A slide-out panel that appears from the side of the screen.
    ├── skeleton.tsx             # A component to display a placeholder preview of content before it loads.
    ├── sonner.tsx               # A toast notification component, wrapping the 'sonner' library.
    ├── states/                  # Components for representing different application states.
    │   ├── EmptyState.tsx       # A component to show when no data is available.
    │   ├── ErrorState.tsx       # A component to show when an error has occurred.
    │   ├── SkeletonPanel.tsx    # A panel filled with skeleton loading placeholders.
    │   └── index.ts             # Exports all state components.
    ├── switch.tsx               # A two-state toggle switch component.
    ├── table.tsx                # Components for creating and styling data tables.
    ├── tabs.tsx                 # A set of layered sections of content, known as tab panels, that are displayed one at a time.
    ├── textarea.tsx             # A multi-line text input component.
    ├── toggle.tsx               # A two-state button that can be either on or off.
    └── tooltip.tsx              # A small pop-up that displays information when a user hovers over an element.