# Component Documentation

This documentation provides a comprehensive reference for the components available in the repository. It details the purpose, styling, and usage of components across Authentication, Shell, Shared, and UI libraries.

## Auth Components
Located in `auth/`

### ForgotPasswordForm
A form allowing users to request a password reset link.
*   **Style:** Uses a standard vertical form layout with email validation.
*   **Functionality:** Handles state for `idle`, `submitting`, and `sent`. Includes a countdown/resend logic for the email link.
*   **Usage:** Use on the `/forgot-password` route.

### LoginForm
The primary sign-in interface.
*   **Style:** Vertical stack of inputs (Email, Password, optional Tenant ID) with validation error states.
*   **Functionality:** authenticates users via server actions and redirects to the dashboard or a specified `redirectTo` path.
*   **Usage:** Use on the `/login` route.

### LogoutButton
A client-side trigger for signing out.
*   **Style:** A simple button with a hover state.
*   **Functionality:** Uses `useTransition` to call the logout server endpoint while showing a "Signing out..." pending state.
*   **Usage:** Place in user menus or profile settings.

### RegisterForm
The tenant and user registration interface.
*   **Style:** A comprehensive form including Full Name, Organization, Email, Password, Invite Token (conditional), and Terms acceptance.
*   **Functionality:** Adapts to signup policies (`public`, `invite_only`, `approval`). If the policy dictates, it enforces the presence of an invite token.
*   **Usage:** Use on the `/register` or `/signup` route.

### ResetPasswordForm
The form used when a user clicks a password reset link.
*   **Style:** Two password inputs (New Password, Confirm Password) with validation to ensure they match.
*   **Functionality:** Consumes a token prop to finalize the password reset process via server actions.
*   **Usage:** Use on the `/reset-password` route (requires a token).

### SilentRefresh
A headless component for session management.
*   **Style:** None (renders `null`).
*   **Functionality:** Invokes a hook `useSilentRefresh` to keep the user session active in the background.
*   **Usage:** Include in the root layout or auth provider.

---

## Shared Components
Located in `shared/`

### ConversationDetailDrawer
A slide-over sheet displaying metadata for a chat transcript.
*   **Style:** A right-aligned `Sheet` containing glass panels and key-value lists.
*   **Functionality:** Shows conversation ID, timestamps, message count, and agent context. Provides actions to **Delete** the transcript or **Export** it as JSON.
*   **Usage:** Use in chat history lists or admin views to inspect conversation details.

---

## Shell Components
Located in `shell/`

### AppMobileNav
The mobile navigation drawer.
*   **Style:** A left-aligned `Sheet` triggered by a "Menu" button.
*   **Functionality:** Renders navigation links and account settings in a scrollable vertical list optimized for touch.
*   **Usage:** Rendered by the layout on small viewports.

### AppNavLinks
The core navigation link renderer.
*   **Style:** Supports `rail` (desktop sidebar) and `mobile` variants. Active links are highlighted with a background and border.
*   **Functionality:** Checks the current pathname to apply active states. Supports optional badges (e.g., notification counts) next to links.
*   **Usage:** Used within `AppSidebar` and `AppMobileNav`.

### AppPageHeading
A standardized header for application pages.
*   **Style:** Combines a breadcrumb trail (e.g., "Acme Console > Dashboard") with a `SectionHeader`.
*   **Functionality:** Automatically determines the active page label based on the current URL and navigation items.
*   **Usage:** Place at the top of main dashboard views.

### AppSidebar
The desktop sidebar navigation.
*   **Style:** A fixed-width (300px), glass-effect panel containing branding, primary navigation, and account management links.
*   **Functionality:** organizing high-level app navigation.
*   **Usage:** Rendered by the dashboard layout on large screens.

### AppUserMenu
The user profile dropdown.
*   **Style:** A pill-shaped trigger showing the user's avatar and name. Expands into a standard dropdown menu.
*   **Functionality:** Provides quick access to Profile, Settings, Billing, and Logout actions.
*   **Usage:** Located in the top navigation bar (`NavBar`) or sidebar.

---

## UI Components

### AI Components
Located in `ui/ai/`

*   **Actions:** A container for small utility buttons (like Copy, Download, Improve) usually found below a message.
*   **Branch:** Manages navigation between different versions of a message (e.g., "Version 1 of 3"). Includes `BranchPrevious` and `BranchNext` buttons.
*   **CodeBlock:** A sophisticated code snippet viewer.
    *   *Features:* Syntax highlighting (Shiki), copy-to-clipboard button, line numbers, and file icons. Supports multiple file tabs if data is provided.
*   **Conversation:** A scrollable container for chat messages that handles "stick-to-bottom" logic automatically. Includes a "Scroll to Bottom" button that appears when the user scrolls up.
*   **Image:** Renders Base64 encoded images generated by AI models.
*   **InlineCitation:** A rich component for citing sources.
    *   *Style:* Renders as a badge or link in the text.
    *   *Interaction:* On hover, opens a card showing a carousel of source details (Title, URL, Description).
*   **Loader:** A minimalist SVG spinner used to indicate AI processing.
*   **Message:** The core chat bubble component.
    *   *Style:* Differentiates visually between `user` (primary color) and `assistant` (secondary/gray) roles.
    *   *Features:* Includes slots for Avatars and Content.
*   **PromptInput:** A highly interactive text area for sending messages.
    *   *Features:* Auto-resizing text area, attachment buttons, model selection dropdown, and a submit button that changes state based on status (idle, streaming, error).
*   **Reasoning:** A collapsible "Chain of Thought" block.
    *   *Usage:* Used to hide verbose AI thinking steps while keeping them accessible.
*   **Response:** A Markdown renderer wrapped around `react-markdown`.
    *   *Features:* "Hardened" to handle incomplete markdown tokens during streaming (e.g., unclosed bold tags) without breaking the layout. Supports math (Katex) and GFM.
*   **Sources:** A collapsible section listing sources used by the AI.
    *   *Style:* Shows a "Used X sources" trigger that expands to a list of links.
*   **Suggestions:** A horizontal scroll area containing chips for suggested follow-up prompts.
*   **Task:** A collapsible item representing a sub-task or tool execution state (e.g., "Locate billing CSV").
*   **Tool:** A detailed view of a tool/function call.
    *   *States:* Displays status badges (Pending, Running, Completed, Error).
    *   *Content:* Shows JSON inputs and outputs/errors in code blocks.
*   **WebPreview:** An iframe wrapper for previewing generated web content. Includes a browser-like navigation bar (Back, Forward, Reload, URL bar) and a collapsible console log viewer.

### Avatar Components
Located in `ui/avatar/`

*   **Avatar:** Basic circular image container with fallback text support.
*   **AvatarGroup:** A component to stack multiple avatars.
    *   *Variants:* `motion` (animated hover spread), `css` (simple overlap), `stack` (cards style).
*   **AnimatedTooltip:** An avatar row where hovering an image reveals a floating tooltip with the user's name and designation.

### Foundation Components
Located in `ui/foundation/`

*   **GlassPanel:** A stylistic container applying a frosted glass effect (backdrop blur), thin border, and subtle shadow. Used heavily in the Shell and Dashboard.
*   **InlineTag:** A small, pill-shaped tag for status or metadata. Supports `default`, `positive`, and `warning` tones.
*   **KeyValueList:** A grid layout for displaying data pairs (Label -> Value). Supports 1 or 2 column layouts.
*   **PasswordPolicyList:** A visual checklist of password requirements (e.g., "At least 12 characters").
*   **SectionHeader:** A standard header component for pages or sections. Includes Title, Description, Eyebrow text, and a slot for Action buttons.
*   **StatCard:** A glass panel designed to show a single key metric. Includes label, large value, icon, and trend indicator (positive/negative percentage).

### Hero Components
Located in `ui/hero/`

*   **HeroGeometric:** A visually striking landing page hero section.
    *   *Style:* Features floating 3D "elegant shapes" with gradients, glassmorphism, and fade-up animations for text.

### Motion Components
Located in `ui/motion/`

*   **Magnetic:** A wrapper component that makes its child element "attract" to the mouse cursor when hovered, creating a playful interactive effect.

### State Components
Located in `ui/states/`

*   **EmptyState:** A placeholder displayed when lists or data are empty. Shows an icon, title, description, and optional action button.
*   **ErrorState:** A placeholder for failed states. Shows a warning icon and a "Try Again" button.
*   **SkeletonPanel:** A loading state component that renders a `GlassPanel` filled with animated skeleton lines.

### Core UI Components
Located in `ui/`

*   **Accordion:** A vertically stacked set of interactive headings that each reveal a section of content.
*   **Alert:** Displays a callout for user attention (Default or Destructive variants).
*   **AlertDialog:** A modal dialog that interrupts the user with important content and expects a response (e.g., Confirm Deletion).
*   **AspectRatio:** Helper to display content within a desired ratio (e.g., 16:9).
*   **Badge:** Small status label or tag.
*   **Banner:** A full-width notification bar, often used for system-wide announcements or warnings.
*   **Beam (`AnimatedBeam`):** An animated SVG line connecting two elements, useful for visualizing data flow or connections.
*   **Breadcrumb:** Navigation trail showing the current page's location in the hierarchy.
*   **Button:** The primary interactive element.
    *   *Variants:* Default, Destructive, Outline, Secondary, Ghost, Link.
    *   *Sizes:* Default, Sm, Lg, Icon.
*   **Card:** A flexible container with Header, Title, Description, Content, and Footer sections.
*   **Carousel:** A slideshow component for cycling through elements.
*   **Checkbox:** A control that allows the user to toggle between checked and unchecked.
*   **Collapsible:** An interactive component which expands/collapses a panel.
*   **Command:** A fast, composable command menu (CMD+K style) for search and navigation.
*   **ContextMenu:** A menu triggered by a right-click on an element.
*   **CopyButton:** A specialized button that copies text to the clipboard and temporarily changes its icon to a checkmark.
*   **DataTable:** A powerful table component based on TanStack Table.
    *   *Features:* Sorting, Pagination, Row selection, Skeleton loading states.
*   **Dialog:** A modal window that overlays the primary content.
*   **DropdownMenu:** Displays a menu to the user—such as a set of actions or functions—triggered by a button.
*   **Dropzone:** A drag-and-drop zone for file uploads. Includes specific visual states for content vs. empty.
*   **Form:** A wrapper around `react-hook-form` that provides context for labels, inputs, validation messages, and descriptions.
*   **HoverCard:** A preview card that pops up when hovering over a link or trigger.
*   **Input:** A basic text field for user input.
*   **Label:** Renders an accessible label associated with controls.
*   **Marquee:** An infinite scrolling horizontal container for logos or text.
*   **NavBar:** A responsive top navigation bar handling logo, links, and user menus.
*   **NavigationMenu:** A collection of links for navigating websites, supporting mega-menu style dropdowns.
*   **Pagination:** Navigation controls for paginated data (Previous, Next, Page Numbers).
*   **Popover:** Displays rich content in a portal, triggered by a button.
*   **Progress:** Displays an indicator showing the completion progress of a task.
*   **RadioGroup:** A set of checkable buttons where only one can be checked at a time.
*   **Resizable:** A layout component that allows panels to be resized (dragged) by the user.
*   **ScrollArea:** Augments native scrolling with custom-styled scrollbars.
*   **Select:** Displays a list of options for the user to pick from—triggered by a button.
*   **Separator:** Visually separates content in a list or group.
*   **Sheet:** Extends the Dialog component to display content that complements the main screen (side drawer).
*   **Skeleton:** Used to show a placeholder while content is loading.
*   **Sonner:** A toast notification provider.
*   **Spinner:** Loading indicators with multiple visual variants (circle, pinwheel, bars, infinite, etc.).
*   **Status:** A compound component (`StatusIndicator`, `StatusLabel`) for displaying system status (Online, Offline, Maintenance).
*   **Switch:** A control that allows the user to toggle between checked and unchecked (toggle switch).
*   **Table:** A responsive HTML table component.
*   **Tabs:** A set of layered sections of content—known as tab panels—that are displayed one at a time.
*   **Testimonials (`AnimatedTestimonials`):** An animated slider for displaying user testimonials with images and quotes.
*   **Textarea:** A multi-line text input field.
*   **ThemeToggle:** A specific dropdown button to toggle between Light, Dark, and System themes.
*   **Toggle:** A two-state button that can be either on or off.
*   **Tooltip:** A popup that displays information related to an element when the element receives keyboard focus or the mouse hovers over it.
*   **VideoPlayer:** A customizable video player wrapper around `media-chrome`, providing consistent controls (Play, Seek, Volume) across browsers.

## Shadcn React Hooks

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
