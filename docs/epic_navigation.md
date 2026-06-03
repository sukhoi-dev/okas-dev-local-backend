# EPIC — WE.OKAS Navigation & Workspace Management
**Platform:** WE.OKAS
**Document Version:** 1.0 | May 28, 2026
**Source:** OKAS Platform — User Stories & Acceptance Criteria

---

## Overview
This epic covers the persistent left navigation bar and sticky UI elements in the WE.OKAS portal. It defines how users access all major modules (Home, Projects, Members, Roles & Permissions, Support, Help) and how the platform logo and Help action remain consistently accessible regardless of navigation length.

---

## STORY 1 — Display WE.OKAS Left Navigation

### User Story
> As a **User**,
> I want to **access all major WE.OKAS modules from the left navigation**,
> So that **I can manage projects, members, permissions, and support workflows efficiently**.

### Acceptance Criteria
71. WE.OKAS displays a persistent left navigation bar throughout the application
72. Left navigation supports the following navigation items:
    - Home
    - Projects
    - Members
    - Roles and Permissions
    - Support
    - Help
73. Each navigation item displays:
    - Icon
    - Label
    - Hover interaction state
    - Selected state indication
74. Clicking navigation items loads the corresponding module successfully
75. Selected navigation item remains visually distinguishable from non-selected items
76. Navigation hierarchy and interactions remain visually consistent with Design Studio navigation behavior
77. Unauthorized or restricted modules are hidden or restricted safely based on user permissions
78. Navigation state remains synchronized correctly during page refreshes and reconnect events
79. Navigation interactions remain responsive during rapid switching between modules
80. System remains stable during simultaneous navigation and module-loading operations

### API Endpoints Required
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/auth/session` | Validate session and fetch user permissions for navigation rendering |
| GET | `/we-okas/navigation` | Fetch authorized navigation items for the current user role |

### Business Rules
- Navigation items visible to a user are determined by their **assigned role permissions**
- Restricted modules must be **hidden from navigation**, not just disabled
- Navigation state (selected item) must persist correctly across page refreshes
- Navigation must remain consistent and functional across all supported screen sizes and resolutions

---

## STORY 2 — Maintain Sticky Logo and Help Navigation Actions

### User Story
> As a **User**,
> I want to **have the platform logo and Help actions remain consistently accessible**,
> So that **I can navigate and access support easily regardless of navigation length**.

### Acceptance Criteria
81. Platform logo remains fixed at the top of the left navigation consistently
82. Help action remains fixed at the bottom of the left navigation consistently
83. Sticky navigation behavior remains stable during navigation scrolling operations
84. Navigation scrolling does not affect accessibility of sticky elements
85. Sticky elements remain visually distinguishable from scrollable navigation items
86. Sticky navigation layout remains responsive across supported screen sizes and resolutions
87. Help action remains accessible regardless of navigation list length
88. Logo interaction behavior remains consistent across modules
89. Sticky navigation elements remain visually aligned during resize and refresh operations
90. System remains stable during simultaneous scrolling and navigation interactions

### Business Rules
- Platform logo (top-sticky) must always be visible and clickable — clicking it should redirect to the Home module
- Help action (bottom-sticky) must always be visible regardless of how long the navigation list grows
- Sticky positioning must not be broken by dynamic navigation items added based on user permissions

---

## Technical Notes

### Components Involved
- Left Navigation Bar (persistent sidebar)
- Navigation Item (icon + label + hover + selected state)
- Sticky Logo (top of sidebar)
- Sticky Help Action (bottom of sidebar)

### Permission Rules
- Navigation items are rendered based on the authenticated user's **role permissions**
- Modules the user does not have access to must be **hidden from navigation entirely**
- Unauthorized direct URL access to restricted modules must return `403 Forbidden`
- Navigation permissions are re-evaluated on session refresh

### Responsive Behavior
- Navigation must remain functional and visually consistent across all supported screen sizes
- Sticky elements (logo and Help) must remain anchored regardless of screen height or navigation length
