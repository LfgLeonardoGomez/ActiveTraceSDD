# UI Components — Spec

> Shared UI component library: Button, Input, Card, Spinner, cn() utility.

---

## REQ-UI-01: Button supports variants (default, destructive, outline, secondary, ghost, link) via CVA

The Button component uses class-variance-authority (CVA) to define visual variants.

### Scenarios

**Scenario 1: Default variant renders with primary styling**
GIVEN the Button is rendered with variant="default" (or no variant prop)
WHEN the component mounts
THEN the button has a solid background color (matching the design system primary color)
AND white text color
AND appropriate hover/focus/active states

**Scenario 2: Destructive variant renders with danger styling**
GIVEN the Button is rendered with variant="destructive"
WHEN the component mounts
THEN the button has a red/danger background color
AND white text
AND appropriate hover/focus states

**Scenario 3: Outline variant renders with border-only styling**
GIVEN the Button is rendered with variant="outline"
WHEN the component mounts
THEN the button has a transparent background
AND a 1px border
AND text matching the border color
AND no background fill on default state

**Scenario 4: Secondary variant renders with muted styling**
GIVEN the Button is rendered with variant="secondary"
WHEN the component mounts
THEN the button has a muted/gray background
AND appropriate contrast text

**Scenario 5: Ghost variant renders with no background or border**
GIVEN the Button is rendered with variant="ghost"
WHEN the component mounts
THEN the button has no background and no border
AND text is the only visible content
AND a subtle hover background appears on interaction

**Scenario 6: Link variant renders as text**
GIVEN the Button is rendered with variant="link"
WHEN the component mounts
THEN the button has no background, no border, no padding (inline appearance)
AND text color matches the primary color
AND text is underlined on hover

---

## REQ-UI-02: Button supports sizes (default, sm, lg, icon) via CVA

The Button component supports multiple size presets.

### Scenarios

**Scenario 1: Default size**
GIVEN the Button is rendered with size="default" (or no size prop)
WHEN the component mounts
THEN the button has standard height (h-9 or h-10)
AND standard horizontal padding (px-4)

**Scenario 2: Small size**
GIVEN the Button is rendered with size="sm"
WHEN the component mounts
THEN the button has reduced height (h-8)
AND reduced horizontal padding (px-3)
AND smaller font size

**Scenario 3: Large size**
GIVEN the Button is rendered with size="lg"
WHEN the component mounts
THEN the button has increased height (h-11)
AND increased horizontal padding (px-8)
AND larger font size

**Scenario 4: Icon size**
GIVEN the Button contains only an icon and is rendered with size="icon"
WHEN the component mounts
THEN the button is a square (equal width and height, h-9 w-9 or similar)
AND has no text label padding
AND the icon is centered within the square

---

## REQ-UI-03: Button disabled state applies pointer-events-none + opacity-50

Disabled buttons are visually distinct and non-interactive.

### Scenarios

**Scenario 1: Disabled button is visually distinct**
GIVEN the Button is rendered with disabled={true}
WHEN the component mounts
THEN the button has opacity-50
AND pointer-events-none is applied (clicks do not register)
AND the button has aria-disabled="true"

**Scenario 2: Disabled button shows loading state**
GIVEN the Button is rendered with isLoading={true}
WHEN the component mounts
THEN the button is disabled (disabled attribute)
AND a Spinner icon replaces or prepends the button text
AND the button text remains visible (Spinner + text, not just Spinner)

**Scenario 3: Disabled button click does not trigger onClick**
GIVEN the Button is disabled
WHEN the user clicks on it
THEN the onClick handler is NOT called
AND no form submission occurs

---

## REQ-UI-04: Input renders with label, error message (aria-invalid + role="alert")

The Input component provides accessible form fields with validation feedback.

### Scenarios

**Scenario 1: Input renders with label**
GIVEN the Input is rendered with a label prop
WHEN the component mounts
THEN a <label> element is rendered above (or to the left of) the input
AND the label is associated with the input via htmlFor/id
AND the input has a visible border and placeholder text

**Scenario 2: Input shows error state**
GIVEN the Input is rendered with an error prop containing a message
WHEN the component mounts
THEN the input element has aria-invalid="true"
AND a <p> or <span> element with role="alert" contains the error message
AND the error message is visually positioned below the input
AND the input border is red/destructive color
AND the error message is red/destructive text

**Scenario 3: Input without error state**
GIVEN the Input is rendered without an error prop
WHEN the component mounts
THEN aria-invalid is not set (or is false)
AND no role="alert" element is rendered
AND the input border is the default neutral color

**Scenario 4: Error message clears when value changes**
GIVEN the Input is displaying an error message
WHEN the user types in the input field
THEN the error message is cleared (parent component controls this via state reset)
AND aria-invalid becomes false

---

## REQ-UI-05: Card components (Card, CardHeader, CardTitle, CardDescription, CardContent, CardFooter) follow compound pattern

The Card component family provides a consistent container layout with named sub-components.

### Scenarios

**Scenario 1: Full card renders all sections**
GIVEN the following compound structure is rendered:
```
<Card>
  <CardHeader>
    <CardTitle>Título</CardTitle>
    <CardDescription>Descripción</CardDescription>
  </CardHeader>
  <CardContent>Contenido</CardContent>
  <CardFooter>Footer</CardFooter>
</Card>
```
WHEN the component mounts
THEN Card has a white/neutral background, border, rounded corners, and shadow
AND CardHeader renders at the top with the title and description
AND CardTitle renders with larger/bold text
AND CardDescription renders with muted/smaller text
AND CardContent renders in the middle with standard padding
AND CardFooter renders at the bottom (separated from content by a border or with different styling)

**Scenario 2: Minimal card without optional sections**
GIVEN the following compound structure is rendered:
```
<Card>
  <CardContent>Solo contenido</CardContent>
</Card>
```
WHEN the component mounts
THEN the Card renders with correct styling (border, rounded corners)
AND only CardContent is visible
AND no empty header or footer space is present

**Scenario 3: CardTitle and CardDescription without CardHeader wrapper**
GIVEN CardTitle and CardDescription are rendered outside CardHeader
WHEN the component mounts
THEN they still render with correct typography styling
AND no structural error occurs

---

## REQ-UI-06: Spinner renders a CSS/animated loading indicator

The Spinner component provides visual feedback during async operations.

### Scenarios

**Scenario 1: Spinner renders with default size**
GIVEN the Spinner is rendered without a size prop
WHEN the component mounts
THEN an animated spinning element is visible
AND the default size is approximately 24x24 pixels (h-6 w-6)
AND the animation is CSS-based (not an external library)
AND the spinner has aria-label="Cargando" for accessibility

**Scenario 2: Spinner renders with custom size**
GIVEN the Spinner is rendered with size="lg"
WHEN the component mounts
THEN the spinning element is approximately 48x48 pixels (h-12 w-12)
AND the animation speed is consistent with the default size

**Scenario 3: Spinner color matches text color by default**
GIVEN the Spinner is rendered without a color override
WHEN the component mounts
THEN the spinner uses currentColor for the border/arc
AND it inherits the text color of its parent

---

## REQ-UI-07: cn() utility merges Tailwind classes using clsx + twMerge

The cn() helper combines class names with proper Tailwind conflict resolution.

### Scenarios

**Scenario 1: cn() merges simple class strings**
GIVEN cn("text-red-500", "bg-blue-100")
WHEN the function is called
THEN it returns "text-red-500 bg-blue-100"

**Scenario 2: cn() resolves conflicting Tailwind classes**
GIVEN cn("px-4", "px-6") — conflicting padding classes
WHEN the function is called
THEN it returns "px-6" (last conflicting class wins, handled by twMerge)

**Scenario 3: cn() handles conditional classes via clsx**
GIVEN cn("base-class", isActive && "active-class", "static-class")
WHEN the function is called with isActive = true
THEN it returns "base-class active-class static-class"
AND when isActive = false, it returns "base-class static-class"

**Scenario 4: cn() handles falsy values gracefully**
GIVEN cn("always", false && "never", undefined, null, 0)
WHEN the function is called
THEN it returns "always" (falsy values are filtered out by clsx)

**Scenario 5: cn() merges Tailwind-specific conflicts correctly**
GIVEN cn("font-bold", "font-medium")
WHEN the function is called
THEN it returns "font-medium" (not "font-bold font-medium")
AND twMerge resolves the Tailwind font-weight conflict properly
