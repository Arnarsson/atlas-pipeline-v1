# Fix TypeScript Skill

Fix common TypeScript errors in the Atlas Pipeline frontend.

## When to Use
- When `npm run build` fails with TypeScript errors
- Before committing frontend changes
- After adding new components

## Instructions

### 1. Run TypeScript Check

```bash
cd /home/user/atlas-pipeline-v1/frontend
npm run build 2>&1 | grep -E "error TS|is declared but"
```

### 2. Common Fixes

#### Unused Variables
Error: `'varName' is declared but its value is never read`

Fix: Prefix with underscore or remove from destructuring
```typescript
// Before
const { data, isLoading, refetch } = useQuery({...})  // refetch unused

// After - Option 1: Remove
const { data, isLoading } = useQuery({...})

// After - Option 2: Prefix
const { data, isLoading, refetch: _refetch } = useQuery({...})
```

#### Unused Function Parameters
Error: `'props' is declared but its value is never read`

Fix: Prefix with underscore
```typescript
// Before
function Component({ onClose }: Props) {  // onClose unused

// After
function Component(_props: Props) {
```

#### JSX.Element Namespace Not Found
Error: `Cannot find namespace 'JSX'`

Fix: Use ReactNode instead
```typescript
// Before
import { useState } from 'react';
const iconMap: Record<string, JSX.Element> = {...}

// After
import { useState, ReactNode } from 'react';
const iconMap: Record<string, ReactNode> = {...}
```

#### Unused Imports
Error: `'SomeComponent' is declared but its value is never read`

Fix: Remove the unused import
```typescript
// Before
import { Button, Card, UnusedComponent } from './components'

// After
import { Button, Card } from './components'
```

### 3. Verify Fix

```bash
cd /home/user/atlas-pipeline-v1/frontend
npm run build
```

Expected: `built in X.XXs` with no errors

## Files Commonly Affected

- `src/pages/*.tsx` - Page components
- `src/components/*.tsx` - Reusable components
- `src/api/client.ts` - API client

## Prevention Tips

1. Enable ESLint in your editor
2. Run `npm run build` before committing
3. Use React Query's `enabled` option instead of conditional refetch
4. Destructure only what you need from hooks
