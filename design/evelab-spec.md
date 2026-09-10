# EveLab Insight Design System — Structured Specification

> Extracted from https://www.evelabinsight.com/en
> Product type: AI skin analysis / beauty-tech SaaS
> Visual tone: clinical, scientific, soft, premium, trustworthy

## Brand Profile

- **Brand name**: EveLab Insight
- **Product type**: beauty-tech / med-tech SaaS
- **Personality**: clinical, evidence-based, premium, calm, trustworthy
- **Color naming prefix**: evelab
- **Source**: structured-spec (website CSS + screenshot analysis)
- **Theme mode**: light-only

## Color Tokens

### Primary (Cyan / Mint)

| Token | Value | Usage |
|-------|-------|-------|
| `--evelab-cyan-50` | `#e6fafb` | lightest tint |
| `--evelab-cyan-100` | `#b3f0f3` | light tint |
| `--evelab-cyan-200` | `#80e6ec` | hover / soft backgrounds |
| `--evelab-cyan-300` | `#4ddce4` | accent highlights |
| `--evelab-cyan-400` | `#26d2dc` | secondary buttons |
| `--evelab-cyan-500` | `#1fc8d2` | **primary brand color** |
| `--evelab-cyan-600` | `#1ab3bc` | primary hover |
| `--evelab-cyan-700` | `#159da5` | pressed |
| `--evelab-cyan-800` | `#10878e` | dark accents |
| `--evelab-cyan-900` | `#0c7178` | darkest |

### Neutral (Warm Zinc)

| Token | Value | Usage |
|-------|-------|-------|
| `--evelab-zinc-50` | `#fafafa` | page background |
| `--evelab-zinc-100` | `#f4f4f5` | card / section background |
| `--evelab-zinc-200` | `#e4e4e7` | borders / dividers |
| `--evelab-zinc-300` | `#d4d4d8` | disabled borders |
| `--evelab-zinc-400` | `#9f9fa9` | muted text |
| `--evelab-zinc-500` | `#71717a` | secondary text |
| `--evelab-zinc-600` | `#52525c` | body text |
| `--evelab-zinc-700` | `#3f3f46` | strong text |
| `--evelab-zinc-800` | `#27272a` | headings |
| `--evelab-zinc-900` | `#09090b` | primary text |

### Amber (Accent / Data highlights)

| Token | Value | Usage |
|-------|-------|-------|
| `--evelab-amber-100` | `#fff3d6` | soft highlights |
| `--evelab-amber-200` | `#ffe4a8` | metric backgrounds |
| `--evelab-amber-300` | `#ffd236` | data highlights |
| `--evelab-amber-400` | `#fcb900` | accent badges |
| `--evelab-amber-500` | `#f99c00` | **accent / CTA metric** |
| `--evelab-amber-600` | `#e07e00` | hover |

### Semantic Aliases

| Token | Value |
|-------|-------|
| `--primary` | `#1fc8d2` |
| `--primary-foreground` | `#ffffff` |
| `--secondary` | `#f4f4f5` |
| `--secondary-foreground` | `#09090b` |
| `--accent` | `#f99c00` |
| `--accent-foreground` | `#ffffff` |
| `--background` | `#f8f8f7` |
| `--foreground` | `#09090b` |
| `--muted` | `#f4f4f5` |
| `--muted-foreground` | `#52525c` |
| `--border` | `#e4e4e7` |
| `--input` | `#ffffff` |
| `--input-border` | `#e4e4e7` |
| `--ring` | `#1fc8d2` |
| `--card` | `#ffffff` |
| `--card-foreground` | `#09090b` |

### Surface Hierarchy

| Token | Value |
|-------|-------|
| `--surface` | `#ffffff` |
| `--surface-dim` | `#f9f8f6` |
| `--surface-container-lowest` | `#f8f8f7` |
| `--surface-container-low` | `#f9f8f6` |
| `--surface-container` | `#ffffff` |
| `--surface-container-high` | `#ffffff` |
| `--surface-container-highest` | `#f4f4f5` |

### Status Colors

| Token | Value |
|-------|-------|
| `--destructive` | `#ef4444` |
| `--destructive-foreground` | `#ffffff` |
| `--success` | `#22c55e` |
| `--success-foreground` | `#ffffff` |
| `--warning` | `#f99c00` |
| `--warning-foreground` | `#ffffff` |

## Typography Tokens

### Font Families

| Token | Stack |
|-------|-------|
| `--font-display` | `"Poppins", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif` |
| `--font-heading` | `"Poppins", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif` |
| `--font-body` | `"Roboto", "PingFang SC", "Hiragino Sans GB", "Microsoft YaHei", sans-serif` |
| `--font-serif` | `"Castoro", Georgia, serif` |

### Font Sizes

| Token | Value |
|-------|-------|
| `--font-size-display` | 56px |
| `--font-size-h1` | 40px |
| `--font-size-h2` | 32px |
| `--font-size-h3` | 24px |
| `--font-size-h4` | 20px |
| `--font-size-lead` | 18px |
| `--font-size-body` | 16px |
| `--font-size-sm` | 14px |
| `--font-size-caption` | 12px |
| `--font-size-eyebrow` | 11px |

### Font Weights

| Token | Value |
|-------|-------|
| `--font-weight-normal` | 400 |
| `--font-weight-medium` | 500 |
| `--font-weight-semibold` | 600 |
| `--font-weight-bold` | 700 |

### Line Heights

| Token | Value |
|-------|-------|
| `--line-height-display` | 1.1 |
| `--line-height-h1` | 1.15 |
| `--line-height-h2` | 1.2 |
| `--line-height-h3` | 1.25 |
| `--line-height-h4` | 1.35 |
| `--line-height-lead` | 1.6 |
| `--line-height-body` | 1.6 |
| `--line-height-sm` | 1.5 |
| `--line-height-caption` | 1.4 |
| `--line-height-eyebrow` | 1.4 |

### Letter Spacing

| Token | Value |
|-------|-------|
| `--letter-spacing-tight` | -0.02em |
| `--letter-spacing-normal` | 0em |
| `--letter-spacing-wide` | 0.05em |
| `--letter-spacing-wider` | 0.1em |

## Spacing Tokens

| Token | Value |
|-------|-------|
| `--space-1` | 4px |
| `--space-2` | 8px |
| `--space-3` | 12px |
| `--space-4` | 16px |
| `--space-5` | 20px |
| `--space-6` | 24px |
| `--space-8` | 32px |
| `--space-10` | 40px |
| `--space-12` | 48px |
| `--space-16` | 64px |
| `--space-20` | 80px |
| `--space-24` | 96px |

## Radius Tokens

| Token | Value |
|-------|-------|
| `--radius-sm` | 4px |
| `--radius-md` | 8px |
| `--radius-lg` | 12px |
| `--radius-xl` | 16px |
| `--radius-2xl` | 20px |
| `--radius-3xl` | 24px |
| `--radius-full` | 9999px |

## Shadow Tokens

| Token | Value | Usage |
|-------|-------|-------|
| `--shadow-1` | `0 1px 2px rgba(0,0,0,0.04), 0 1px 1px rgba(0,0,0,0.03)` | subtle cards |
| `--shadow-2` | `0 2px 8px rgba(0,0,0,0.06), 0 4px 24px rgba(0,0,0,0.04)` | cards / Apple shadow |
| `--shadow-3` | `0 8px 24px rgba(0,0,0,0.08)` | hover / float |
| `--shadow-4` | `0 16px 40px rgba(0,0,0,0.12)` | modals |

## Sizing Tokens

| Token | Value |
|-------|-------|
| `--size-button-height` | 44px |
| `--size-button-height-sm` | 36px |
| `--size-input-height` | 48px |
| `--size-icon-sm` | 16px |
| `--size-icon-md` | 24px |
| `--size-nav-height` | 64px |
| `--max-content-width` | 1280px |

## Motion Tokens

| Token | Value |
|-------|-------|
| `--duration-fast` | 150ms |
| `--duration-normal` | 250ms |
| `--duration-slow` | 350ms |
| `--ease-out` | `cubic-bezier(0,0,0.2,1)` |
| `--ease-in-out` | `cubic-bezier(0.4,0,0.2,1)` |

## Component Patterns

### Button

- **Primary**: bg `#1fc8d2`, white text, height 44px, padding 0 24px, radius 9999px, font-weight 500, hover `#1ab3bc`
- **Secondary / Outline**: white bg, 1px `#09090b` border, black text, height 44px, radius 9999px, hover light gray fill
- **Ghost**: transparent bg, black text, hover light gray fill

### Input

- Height 48px, white bg, 1px `#e4e4e7` border, radius 9999px, placeholder `#9f9fa9`
- Focus: ring 2px `#1fc8d2`

### Card

- White bg, radius 20px, shadow-2, padding 24px
- News cards: large media radius 20px, bottom text area

### Tab / Pill Switcher

- Pill container with soft background, active tab white bg with shadow, radius 9999px

### Link

- Default black, hover primary cyan, arrow icon on external / "VIEW ALL" links

### Eyebrow Text

- Uppercase, letter-spacing 0.1em, font-size 11px, font-weight 500, muted color
