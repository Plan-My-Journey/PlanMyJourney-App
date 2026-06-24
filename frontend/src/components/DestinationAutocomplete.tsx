import { useEffect, useState } from "react";

import { api } from "../api/client";

type Suggestion = {
  label: string;
  city: string;
};

type Props = {
  readonly id?: string;
  readonly value: string;
  readonly onChange: (value: string) => void;
  readonly placeholder?: string;
  readonly required?: boolean;
};

export default function DestinationAutocomplete({ id, value, onChange, placeholder, required }: Props) {
  const [query, setQuery] = useState(value);
  const [suggestions, setSuggestions] = useState<Suggestion[]>([]);
  const [open, setOpen] = useState(false);

  useEffect(() => {
    setQuery(value);
  }, [value]);

  useEffect(() => {
    const trimmed = query.trim();
    if (trimmed.length < 3) {
      setSuggestions([]);
      return;
    }

    const timer = globalThis.setTimeout(async () => {
      try {
        const { data } = await api.get<{ suggestions: Suggestion[] }>("/utility/geocode/autocomplete", {
          params: { text: trimmed, limit: 5 }
        });
        setSuggestions(data.suggestions ?? []);
        setOpen(true);
      } catch {
        setSuggestions([]);
      }
    }, 350);

    return () => globalThis.clearTimeout(timer);
  }, [query]);

  return (
    <div className="relative">
      <input
        id={id}
        className="field"
        value={query}
        placeholder={placeholder}
        required={required}
        autoComplete="off"
        onChange={(event) => {
          setQuery(event.target.value);
          onChange(event.target.value);
        }}
        onFocus={() => suggestions.length > 0 && setOpen(true)}
        onBlur={() => globalThis.setTimeout(() => setOpen(false), 150)}
      />
      {open && suggestions.length > 0 && (
        <ul className="absolute z-20 mt-1 max-h-48 w-full overflow-auto rounded-lg border border-zinc-200 bg-white shadow-lg">
          {suggestions.map((suggestion) => (
            <li key={`${suggestion.label}-${suggestion.city}`}>
              <button
                type="button"
                className="block w-full px-3 py-2 text-left text-sm hover:bg-zinc-50"
                onMouseDown={(event) => event.preventDefault()}
                onClick={() => {
                  const nextValue = suggestion.city || suggestion.label;
                  setQuery(nextValue);
                  onChange(nextValue);
                  setOpen(false);
                }}
              >
                {suggestion.label}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  );
}
