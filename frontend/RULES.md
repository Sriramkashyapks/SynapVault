# SynapVault Frontend — Developer Guidelines

These guidelines ensure a clean, maintainable, and scalable Next.js codebase, balancing enterprise patterns with solo-developer agility.

---

## 1. Naming Conventions

| What | Case | Example |
| --- | --- | --- |
| React Component | `PascalCase.tsx` | `FileUpload.tsx` |
| Hook | `useCamelCase.ts` | `useDocumentUpload.ts` |
| Zustand Store | `useXxxStore.ts` | `useChatStore.ts` |
| Utility/Helper | `camelCase.ts` | `formatDate.ts` |
| Type/Interface | `PascalCase` | `DocumentMetadata` |
| Route Folder | `kebab-case/` | `app/chat-dashboard/` |

**Rules:**
* No abbreviations (`document` instead of `doc`).
* Keep the module domains consistent (e.g., if you have `components/chat`, keep hooks in `hooks/chat`).

---

## 2. Component Architecture

* **UI Primitives:** Use a design system (like shadcn/ui). Don't build buttons from scratch if a primitive exists.
* **Component Granularity:** One *primary* component per file. Small helper components can remain in the same file when tightly coupled (e.g., `ChatMessage` and `TypingIndicator` inside `ChatWindow.tsx`).
* **Separation of Concerns:** Components should focus on rendering. Move complex business logic into custom hooks (`useXxx.ts`).
* **Error & Loading States:** Always account for `isLoading`, empty states, and errors. A skeleton loader is better than a blank screen.

---

## 3. Data Fetching & State

| Kind of State | Recommended Tool |
| --- | --- |
| Server Data / API | React Query (or SWR) |
| Global UI State | Zustand |
| Component Local | `useState` / `useReducer` |

* **API Calls:** Do not inline `fetch` or `axios` inside components. Create a service file (e.g., `services/DocumentService.ts`) and call it via a React Query hook (`useQuery(...)`).
* **Zustand:** Keep stores atomic. Don't put authentication, chat, theme, and upload all inside one store.

---

## 4. Styling (Tailwind CSS)

* **Utility-First & Tokens:** Use Tailwind design tokens (e.g., `bg-background`, `text-muted-foreground`, `bg-primary`) rather than hardcoded hex values (`bg-[#0F172A]`) to support themes effortlessly.
* **Dynamic Classes:** Use `clsx` or `tailwind-merge` (often aliased as `cn()`) to handle conditional class logic cleanly.

---

## 5. TypeScript & Quality

* **Strict TypeScript:** `strict: true` must be maintained.
* **Types:** Avoid `any`. Use `unknown`, generics, interfaces, and type narrowing.
* **Linting & Formatting:** Ensure code is checked with `eslint` and formatted with `prettier` before pushing.

---

## 6. Pre-Push Checklist

- [ ] Removed all `console.log`s used for debugging.
- [ ] No TypeScript errors or `any` types.
- [ ] UI gracefully handles empty, loading, and error states.
- [ ] Code is linted (`eslint`) and formatted (`prettier`).
