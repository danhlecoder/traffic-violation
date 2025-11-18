# 🎨 FRONTEND COMPONENTS - PROMPT

## 📋 Metadata
```yaml
tags: [frontend, react, components, ui, typescript]
inputs:
  - component_type
  - props_data
  - state_requirements
tools:
  - React 18
  - TypeScript
  - TailwindCSS
  - shadcn/ui
output_format: React components
complexity: Medium
```

---

## 🎯 Component Structure Overview

### Vị trí: `frontend/src/components/`

### Component Categories:
1. **Layout Components** - Header, Sidebar, Layout
2. **Camera Components** - CameraTile, CameraGrid, CameraControls
3. **Violation Components** - ViolationCard, ViolationList, ViolationDetail
4. **UI Components** - Buttons, Modals, Forms (từ shadcn/ui)
5. **Utility Components** - Loading, Error, Empty states

---

## 📊 Main Components Checklist

### 1. CameraTile
**Chức năng**: Hiển thị live stream từ 1 camera

**Props**:
- [ ] `camera_id` - Camera identifier
- [ ] `stream_url` - MJPEG stream URL
- [ ] `status` - active/inactive
- [ ] `onCameraClick` - Click handler

**State**:
- [ ] `isLoading` - Stream loading state
- [ ] `hasError` - Stream error state
- [ ] `violations` - Recent violations list

**UI Elements**:
- [ ] Video stream display
- [ ] Camera name overlay
- [ ] Status indicator (dot)
- [ ] Violation count badge
- [ ] Controls (settings, fullscreen)

**Checklist**:
- [ ] Handle stream connection errors
- [ ] Show loading skeleton
- [ ] Auto-reconnect on disconnect
- [ ] Refresh stream button
- [ ] Responsive layout

---

### 2. ViolationCard
**Chức năng**: Display single violation

**Props**:
- [ ] `violation` - Violation object
- [ ] `onClick` - Click handler
- [ ] `showActions` - Show action buttons

**Display Elements**:
- [ ] Evidence image thumbnail
- [ ] Violation type badge
- [ ] License plate text
- [ ] Timestamp
- [ ] Camera name
- [ ] Status indicator

**Actions**:
- [ ] View details
- [ ] Confirm violation
- [ ] Reject violation
- [ ] Export evidence

**Checklist**:
- [ ] Image lazy loading
- [ ] Handle missing images
- [ ] Color coding by status
- [ ] Hover effects
- [ ] Mobile responsive

---

### 3. RegionEditorModal
**Chức năng**: Draw và edit ROI regions

**Props**:
- [ ] `isOpen` - Modal open state
- [ ] `camera` - Camera object
- [ ] `onSave` - Save handler
- [ ] `onClose` - Close handler

**Features**:
- [ ] Canvas overlay trên stream
- [ ] Draw polygon tool
- [ ] Draw line tool
- [ ] Edit existing ROI
- [ ] Delete ROI
- [ ] ROI metadata (name, type)

**Checklist**:
- [ ] Mouse/touch events
- [ ] Undo/redo functionality
- [ ] Validation (min 3 points)
- [ ] Save confirmation
- [ ] Preview mode
- [ ] Coordinate normalization

---

### 4. ViolationList
**Chức năng**: Paginated list of violations

**Props**:
- [ ] `filters` - Filter object
- [ ] `onFilterChange` - Filter change handler

**Features**:
- [ ] Infinite scroll hoặc pagination
- [ ] Filters (camera, type, status, date)
- [ ] Sort options
- [ ] Search by plate
- [ ] Bulk actions

**State**:
- [ ] `violations` - Data array
- [ ] `page` - Current page
- [ ] `hasMore` - More data flag
- [ ] `isLoading` - Loading state

**Checklist**:
- [ ] Efficient rendering (virtualization)
- [ ] Loading states
- [ ] Empty state message
- [ ] Error handling
- [ ] Refresh data

---

### 5. CameraGrid
**Chức năng**: Grid layout nhiều cameras

**Props**:
- [ ] `cameras` - Array of cameras
- [ ] `layout` - Grid layout (2x2, 3x3, 4x4)
- [ ] `onCameraSelect` - Selection handler

**Features**:
- [ ] Responsive grid
- [ ] Auto layout adjustment
- [ ] Single camera focus mode
- [ ] Fullscreen mode

**Checklist**:
- [ ] Dynamic grid sizing
- [ ] Performance với nhiều streams
- [ ] Handle camera offline
- [ ] Smooth transitions

---

## ✅ Component Best Practices

### 1. Props Validation
- [ ] Use TypeScript interfaces
- [ ] Define PropTypes (nếu JS)
- [ ] Required vs optional props
- [ ] Default props values

### 2. State Management
- [ ] Local state cho UI only
- [ ] Context cho shared state
- [ ] Avoid prop drilling
- [ ] Use custom hooks

### 3. Performance
- [ ] Memoize expensive computations
- [ ] Use React.memo cho pure components
- [ ] Lazy load components
- [ ] Code splitting

### 4. Styling
- [ ] Use TailwindCSS utilities
- [ ] Consistent spacing (4, 8, 16, 24)
- [ ] Color scheme (primary, secondary, accent)
- [ ] Dark mode support (optional)

### 5. Accessibility
- [ ] Semantic HTML
- [ ] ARIA labels
- [ ] Keyboard navigation
- [ ] Screen reader support

---

## ⚠️ Common Pitfalls

### 1. Component quá lớn
❌ **Sai**: 1 component 500+ lines
✅ **Đúng**: Break thành smaller components

### 2. Inline styles thay vì TailwindCSS
❌ **Sai**: `style={{margin: '10px'}}`
✅ **Đúng**: `className="m-2.5"`

### 3. Không handle loading/error states
❌ **Sai**: Assume data luôn có
✅ **Đúng**: Show loading spinner, error message

### 4. Direct DOM manipulation
❌ **Sai**: `document.getElementById()`
✅ **Đúng**: Use refs hoặc React state

### 5. Không optimize re-renders
❌ **Sai**: Component re-render không cần thiết
✅ **Đúng**: useMemo, useCallback, React.memo

### 6. Hardcode API URLs
❌ **Sai**: `fetch('http://localhost:8000/api')`
✅ **Đúng**: Use environment variables

---

## 📝 Component Template

### Functional Component với TypeScript
```
Checklist khi tạo component mới:
- [ ] Define interface cho Props
- [ ] Use functional component syntax
- [ ] Add PropTypes/TypeScript types
- [ ] Implement error boundaries
- [ ] Add loading states
- [ ] Handle empty data
- [ ] Export component
- [ ] Add to index file
```

### Custom Hooks
```
Common hooks:
- useCamera() - Fetch camera data
- useViolations() - Fetch violations
- useWebSocket() - WebSocket connection
- useInterval() - Polling logic
```

---

## 🎨 Styling Guidelines

### TailwindCSS Classes

**Spacing**:
- `p-4` - padding 1rem
- `m-2` - margin 0.5rem
- `space-x-4` - gap giữa children

**Layout**:
- `flex`, `grid` - Layout systems
- `justify-center`, `items-center` - Alignment
- `w-full`, `h-screen` - Sizing

**Colors**:
- `bg-blue-500` - Background
- `text-gray-700` - Text color
- `border-red-300` - Border color

**Responsive**:
- `sm:`, `md:`, `lg:`, `xl:` - Breakpoints
- Mobile-first approach

---

## 🧪 Testing Checklist

### Unit Tests
- [ ] Component renders correctly
- [ ] Props passed correctly
- [ ] Events trigger handlers
- [ ] Conditional rendering works

### Integration Tests
- [ ] API calls work
- [ ] State updates correctly
- [ ] Navigation works
- [ ] Forms submit correctly

### Visual Tests
- [ ] Responsive on mobile
- [ ] Responsive on tablet
- [ ] Responsive on desktop
- [ ] Dark mode (nếu có)
- [ ] Different browsers

---

## 📊 State Management Patterns

### Local State (useState)
**Use for**: UI-only state (dropdown open/close, modal visibility)

### Context API
**Use for**: Shared state (user auth, theme, settings)

### Custom Hooks
**Use for**: Reusable logic (fetch data, WebSocket)

### External State (optional)
**Libraries**: Zustand, Redux (nếu cần complex state)

---

## 🔗 Related Prompts

- `frontend/services.prompt.md` - API integration
- `frontend/state-management.prompt.md` - State patterns
- `api/*.prompt.md` - Backend APIs consumed
- `workflows/new-feature.prompt.md` - Add new components
