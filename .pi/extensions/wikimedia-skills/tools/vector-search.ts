/**
 * wikidata_vector_search — pi custom tool
 *
 * Searches Wikidata items by semantic meaning, concept, or natural-language
 * description using the Wikidata Vector Database at wd-vectordb.wmcloud.org.
 *
 * The Vector Database stores embeddings for every Wikidata entity. When you
 * submit a query, it runs vector similarity + BM25 keyword search in parallel,
 * then merges results with Reciprocal Rank Fusion (RRF).
 *
 * Supports 140+ languages. For 'ar', 'de', 'en', and 'fr', searches within
 * that language's dedicated embeddings. For all others, the query is
 * machine-translated to English first.
 *
 * @see https://wd-vectordb.wmcloud.org
 */

import type { ExtensionAPI } from "@earendil-works/pi-coding-agent";
import { Type } from "typebox";

const VECTOR_DB_URL = "https://wd-vectordb.wmcloud.org/item/query/";
const DEFAULT_LIMIT = 10;
const MAX_LIMIT = 50;

interface VectorResult {
  QID: string;
  similarity_score?: number;
  rrf_score?: number;
  source?: string;
}

/**
 * Format a list of VectorResult objects into a readable TSV table.
 * Shows QID, similarity score, and source (vector/keyword/both).
 */
export function formatResults(results: VectorResult[]): string {
  if (results.length === 0) return "QID\tsimilarity\tsource";
  const rows = results.map((r) => {
    const score = r.similarity_score != null ? r.similarity_score.toFixed(4) : "-";
    const source = r.source ?? "";
    return `${r.QID}\t${score}\t${source}`;
  });
  return `QID\tsimilarity\tsource\n${rows.join("\n")}`;
}

/**
 * Register the wikidata_vector_search custom tool with pi.
 *
 * @param pi - The ExtensionAPI instance
 * @param resolveUA - Function that returns the current User-Agent string
 */
export function registerVectorSearchTool(
  pi: ExtensionAPI,
  resolveUA: () => string,
): void {
  pi.registerTool({
    name: "wikidata_vector_search",
    label: "Wikidata Vector Search",
    description:
      "Search Wikidata items by semantic meaning, concept, or natural language description. " +
      "Returns QIDs with similarity scores. " +
      "Use when you need to find a Wikidata item by what it means rather than by exact label match. " +
      "Supports 140+ languages. " +
      "For example: 'marine biologist who wrote about conservation', 'capital of France', " +
      "'author of The Hitchhiker\\'s Guide to the Galaxy'.",
    promptSnippet: "Semantic Wikidata search by meaning or description",
    promptGuidelines: [
      "Use wikidata_vector_search to find QIDs when you don't know the exact label — describe what you're looking for in natural language.",
      "Set lang='all' (default) for cross-lingual results; set a specific code ('en','de','ar','fr') to constrain to one language.",
      "Set rerank=true when precision matters more than speed (adds ~1s latency).",
    ],
    parameters: Type.Object({
      query: Type.String({
        description:
          "Natural language query — describe the concept, entity, or thing you're looking for. " +
          "Examples: 'marine biologist who wrote about conservation', 'Douglas Adams', 'capital of France'.",
      }),
      lang: Type.Optional(
        Type.String({
          description:
            "Language code. 'all' (default) searches everything. " +
            "'en', 'de', 'ar', 'fr' search within dedicated embeddings for that language.",
          default: "all",
        }),
      ),
      limit: Type.Optional(
        Type.Integer({
          description: "Maximum number of results to return",
          default: DEFAULT_LIMIT,
          minimum: 1,
          maximum: MAX_LIMIT,
        }),
      ),
      rerank: Type.Optional(
        Type.Boolean({
          description:
            "Apply cross-encoder reranker for improved relevance. " +
            "Slower but more accurate. Default: false.",
          default: false,
        }),
      ),
    }),
    async execute(toolCallId, params, signal, onUpdate, ctx) {
      // Build URL with query parameters
      const url = new URL(VECTOR_DB_URL);
      url.searchParams.set("query", params.query);
      url.searchParams.set("K", String(params.limit ?? DEFAULT_LIMIT));
      url.searchParams.set("lang", params.lang ?? "all");
      if (params.rerank) {
        url.searchParams.set("rerank", "true");
      }

      const ua = resolveUA();

      // Notify the user we're fetching
      onUpdate?.({
        content: [
          {
            type: "text",
            text: `Searching Wikidata for "${params.query}"...`,
          },
        ],
      });

      let response: Response;
      try {
        response = await fetch(url.toString(), {
          headers: {
            "User-Agent": ua,
            Accept: "application/json",
          },
          signal,
        });
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : String(err);
        return {
          content: [
            {
              type: "text",
              text: `Vector search request failed: ${message}`,
            },
          ],
          isError: true,
        };
      }

      if (!response.ok) {
        let body = "";
        try {
          body = await response.text();
        } catch {
          body = "(could not read response body)";
        }
        return {
          content: [
            {
              type: "text",
              text:
                `Vector search failed: HTTP ${response.status} ${response.statusText}\n` +
                `URL: ${url.toString()}\n` +
                `Response: ${body.slice(0, 500)}`,
            },
          ],
          isError: true,
        };
      }

      let data: unknown;
      try {
        data = await response.json();
      } catch (err: unknown) {
        const message = err instanceof Error ? err.message : String(err);
        return {
          content: [
            {
              type: "text",
              text: `Failed to parse vector search response as JSON: ${message}`,
            },
          ],
          isError: true,
        };
      }

      // The API returns an array directly, or may wrap it in { results: [...] }
      const results: VectorResult[] = Array.isArray(data)
        ? data
        : Array.isArray((data as Record<string, unknown>).results)
          ? (data as Record<string, unknown>).results as VectorResult[]
          : [];

      if (results.length === 0) {
        return {
          content: [
            {
              type: "text",
              text: `No results found for "${params.query}". Try rephrasing or using a different language.`,
            },
          ],
        };
      }

      const table = formatResults(results);

      // Build a summary line
      const topQID = results[0].QID;
      const topScore = results[0].similarity_score?.toFixed(4) ?? "-";
      const summary = `Found ${results.length} result(s) for "${params.query}". Best match: ${topQID} (score=${topScore})`;

      return {
        content: [
          {
            type: "text",
            text: `${summary}\n\n${table}`,
          },
        ],
      };
    },
  });
}
