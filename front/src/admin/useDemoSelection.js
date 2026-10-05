import { ref, watch } from "vue";
import { useRoute } from "vue-router";

// Les liens entre les vues peuvent cibler un exemple précis (?id=...).
export function useDemoSelection(rows) {
  const route = useRoute();
  const selected = ref(
    rows.find((row) => String(row.id) === route.query.id) || rows[0] || null,
  );
  watch(
    () => route.query.id,
    (id) => {
      if (id)
        selected.value = rows.find((row) => String(row.id) === id) || rows[0];
    },
  );
  return selected;
}
