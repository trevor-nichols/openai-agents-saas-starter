'use client';

import { cn } from '@/lib/utils';
import type { ComponentProps, HTMLAttributes } from 'react';
import { isValidElement, memo } from 'react';
import type { Annotation, ContainerFileCitation, FileCitation, UrlCitation } from '@/lib/chat/types';
import { Sources, SourcesContent, SourcesTrigger, Source } from './source';
import ReactMarkdown, { type Options } from 'react-markdown';
import rehypeKatex from 'rehype-katex';
import remarkGfm from 'remark-gfm';
import remarkMath from 'remark-math';
import { CodeBlock, CodeBlockCopyButton } from './code-block';
import hardenReactMarkdown from 'harden-react-markdown';


/**
 * Parses markdown text and removes incomplete tokens to prevent partial rendering
 * of links, images, bold, and italic formatting during streaming.
 */
function parseIncompleteMarkdown(text: string): string {
  if (!text || typeof text !== 'string') {
    return '';
  }

  let result = text;

  // Handle incomplete links and images
  // Pattern: [...] or ![...] where the closing ] is missing
  const linkImagePattern = /(!?\[)([^\]]*?)$/;
  const linkMatch = result.match(linkImagePattern);
  if (linkMatch && linkMatch[1]) {
    // If we have an unterminated [ or ![, remove it and everything after
    const startIndex = result.lastIndexOf(linkMatch[1]);
    result = result.substring(0, startIndex);
  }

  // Handle incomplete bold formatting (**)
  const boldPattern = /(\*\*)([^*]*?)$/;
  const boldMatch = result.match(boldPattern);
  if (boldMatch) {
    // Count the number of ** in the entire string
    const asteriskPairs = (result.match(/\*\*/g) || []).length;
    // If odd number of **, we have an incomplete bold - complete it
    if (asteriskPairs % 2 === 1) {
      result = `${result}**`;
    }
  }

  // Handle incomplete italic formatting (__)
  const italicPattern = /(__)([^_]*?)$/;
  const italicMatch = result.match(italicPattern);
  if (italicMatch) {
    // Count the number of __ in the entire string
    const underscorePairs = (result.match(/__/g) || []).length;
    // If odd number of __, we have an incomplete italic - complete it
    if (underscorePairs % 2 === 1) {
      result = `${result}__`;
    }
  }

  // Handle incomplete single asterisk italic (*)
  const singleAsteriskPattern = /(\*)([^*]*?)$/;
  const singleAsteriskMatch = result.match(singleAsteriskPattern);
  if (singleAsteriskMatch) {
    // Count single asterisks that aren't part of **
    const singleAsterisks = result.split('').reduce((acc, char, index) => {
      if (char === '*') {
        // Check if it's part of a ** pair
        const prevChar = result[index - 1];
        const nextChar = result[index + 1];
        if (prevChar !== '*' && nextChar !== '*') {
          return acc + 1;
        }
      }
      return acc;
    }, 0);

    // If odd number of single *, we have an incomplete italic - complete it
    if (singleAsterisks % 2 === 1) {
      result = `${result}*`;
    }
  }

  // Handle incomplete single underscore italic (_)
  const singleUnderscorePattern = /(_)([^_]*?)$/;
  const singleUnderscoreMatch = result.match(singleUnderscorePattern);
  if (singleUnderscoreMatch) {
    // Count single underscores that aren't part of __
    const singleUnderscores = result.split('').reduce((acc, char, index) => {
      if (char === '_') {
        // Check if it's part of a __ pair
        const prevChar = result[index - 1];
        const nextChar = result[index + 1];
        if (prevChar !== '_' && nextChar !== '_') {
          return acc + 1;
        }
      }
      return acc;
    }, 0);

    // If odd number of single _, we have an incomplete italic - complete it
    if (singleUnderscores % 2 === 1) {
      result = `${result}_`;
    }
  }

  // Handle incomplete inline code blocks (`) - but avoid code blocks (```)
  const inlineCodePattern = /(`)([^`]*?)$/;
  const inlineCodeMatch = result.match(inlineCodePattern);
  if (inlineCodeMatch) {
    // Check if we're dealing with a code block (triple backticks)
    const allTripleBackticks = (result.match(/```/g) || []).length;

    // If we have an odd number of ``` sequences, we're inside an incomplete code block
    // In this case, don't complete inline code
    const insideIncompleteCodeBlock = allTripleBackticks % 2 === 1;

    if (!insideIncompleteCodeBlock) {
      // Count the number of single backticks that are NOT part of triple backticks
      let singleBacktickCount = 0;
      for (let i = 0; i < result.length; i++) {
        if (result[i] === '`') {
          // Check if this backtick is part of a triple backtick sequence
          const isTripleStart = result.substring(i, i + 3) === '```';
          const isTripleMiddle =
            i > 0 && result.substring(i - 1, i + 2) === '```';
          const isTripleEnd = i > 1 && result.substring(i - 2, i + 1) === '```';

          if (!(isTripleStart || isTripleMiddle || isTripleEnd)) {
            singleBacktickCount++;
          }
        }
      }

      // If odd number of single backticks, we have an incomplete inline code - complete it
      if (singleBacktickCount % 2 === 1) {
        result = `${result}\``;
      }
    }
  }

  // Handle incomplete strikethrough formatting (~~)
  const strikethroughPattern = /(~~)([^~]*?)$/;
  const strikethroughMatch = result.match(strikethroughPattern);
  if (strikethroughMatch) {
    // Count the number of ~~ in the entire string
    const tildePairs = (result.match(/~~/g) || []).length;
    // If odd number of ~~, we have an incomplete strikethrough - complete it
    if (tildePairs % 2 === 1) {
      result = `${result}~~`;
    }
  }

  return result;
}

// Create a hardened version of ReactMarkdown
const HardenedMarkdown = hardenReactMarkdown(ReactMarkdown);

export type ResponseProps = HTMLAttributes<HTMLDivElement> & {
  options?: Options;
  children: Options['children'];
  allowedImagePrefixes?: ComponentProps<
    ReturnType<typeof hardenReactMarkdown>
  >['allowedImagePrefixes'];
  allowedLinkPrefixes?: ComponentProps<
    ReturnType<typeof hardenReactMarkdown>
  >['allowedLinkPrefixes'];
  defaultOrigin?: ComponentProps<
    ReturnType<typeof hardenReactMarkdown>
  >['defaultOrigin'];
  parseIncompleteMarkdown?: boolean;
  citations?: Annotation[] | null;
};

const components: Options['components'] = {
  ol: ({ node: _node, children, className, ...props }) => (
    <ol className={cn('ml-4 list-outside list-decimal', className)} {...props}>
      {children}
    </ol>
  ),
  li: ({ node: _node, children, className, ...props }) => (
    <li className={cn('py-1', className)} {...props}>
      {children}
    </li>
  ),
  ul: ({ node: _node, children, className, ...props }) => (
    <ul className={cn('ml-4 list-outside list-disc', className)} {...props}>
      {children}
    </ul>
  ),
  hr: ({ node: _node, className, ...props }) => (
    <hr className={cn('my-6 border-border', className)} {...props} />
  ),
  strong: ({ node: _node, children, className, ...props }) => (
    <span className={cn('font-semibold', className)} {...props}>
      {children}
    </span>
  ),
  a: ({ node: _node, children, className, ...props }) => (
    <a
      className={cn('font-medium text-primary underline', className)}
      rel="noreferrer"
      target="_blank"
      {...props}
    >
      {children}
    </a>
  ),
  h1: ({ node: _node, children, className, ...props }) => (
    <h1
      className={cn('mt-6 mb-2 font-semibold text-3xl', className)}
      {...props}
    >
      {children}
    </h1>
  ),
  h2: ({ node: _node, children, className, ...props }) => (
    <h2
      className={cn('mt-6 mb-2 font-semibold text-2xl', className)}
      {...props}
    >
      {children}
    </h2>
  ),
  h3: ({ node: _node, children, className, ...props }) => (
    <h3 className={cn('mt-6 mb-2 font-semibold text-xl', className)} {...props}>
      {children}
    </h3>
  ),
  h4: ({ node: _node, children, className, ...props }) => (
    <h4 className={cn('mt-6 mb-2 font-semibold text-lg', className)} {...props}>
      {children}
    </h4>
  ),
  h5: ({ node: _node, children, className, ...props }) => (
    <h5
      className={cn('mt-6 mb-2 font-semibold text-base', className)}
      {...props}
    >
      {children}
    </h5>
  ),
  h6: ({ node: _node, children, className, ...props }) => (
    <h6 className={cn('mt-6 mb-2 font-semibold text-sm', className)} {...props}>
      {children}
    </h6>
  ),
  table: ({ node: _node, children, className, ...props }) => (
    <div className="my-4 overflow-x-auto">
      <table
        className={cn('w-full border-collapse border border-border', className)}
        {...props}
      >
        {children}
      </table>
    </div>
  ),
  thead: ({ node: _node, children, className, ...props }) => (
    <thead className={cn('bg-muted/50', className)} {...props}>
      {children}
    </thead>
  ),
  tbody: ({ node: _node, children, className, ...props }) => (
    <tbody className={cn('divide-y divide-border', className)} {...props}>
      {children}
    </tbody>
  ),
  tr: ({ node: _node, children, className, ...props }) => (
    <tr className={cn('border-border border-b', className)} {...props}>
      {children}
    </tr>
  ),
  th: ({ node: _node, children, className, ...props }) => (
    <th
      className={cn('px-4 py-2 text-left font-semibold text-sm', className)}
      {...props}
    >
      {children}
    </th>
  ),
  td: ({ node: _node, children, className, ...props }) => (
    <td className={cn('px-4 py-2 text-sm', className)} {...props}>
      {children}
    </td>
  ),
  blockquote: ({ node: _node, children, className, ...props }) => (
    <blockquote
      className={cn(
        'my-4 border-muted-foreground/30 border-l-4 pl-4 text-muted-foreground italic',
        className
      )}
      {...props}
    >
      {children}
    </blockquote>
  ),
  code: ({ node, className, ...props }) => {
    const inline = node?.position?.start.line === node?.position?.end.line;

    if (!inline) {
      return <code className={className} {...props} />;
    }

    return (
      <code
        className={cn(
          'rounded bg-muted px-1.5 py-0.5 font-mono text-sm',
          className
        )}
        {...props}
      />
    );
  },
  pre: ({ node: _node, className, children }) => {
    let language = 'javascript';

    if (typeof _node?.properties?.className === 'string') {
      language = _node.properties.className.replace('language-', '');
    }

    // Extract code content from children safely
    let code = '';
    if (
      isValidElement(children) &&
      children.props &&
      typeof (children.props as Record<string, unknown>).children === 'string'
    ) {
      code = (children.props as Record<string, unknown>).children as string;
    } else if (typeof children === 'string') {
      code = children;
    }

    return (
      <CodeBlock
        className={cn('my-4 h-auto', className)}
        code={code}
        language={language}
      >
        <CodeBlockCopyButton
          onCopy={() => console.log('Copied code to clipboard')}
          onError={() => console.error('Failed to copy code to clipboard')}
        />
      </CodeBlock>
    );
  },
};

type FootnoteInjectionResult = {
  markdown: string;
  sources: {
    label: string;
    title?: string | null;
    url?: string | null;
    filename?: string | null;
    file_id?: string | null;
    container_id?: string | null;
  }[];
};

function buildDownloadHref(entry: { file_id?: string | null; container_id?: string | null }) {
  if (entry.file_id && entry.container_id) {
    return `/api/v1/openai/containers/${entry.container_id}/files/${entry.file_id}/download`;
  }
  if (entry.file_id) {
    return `/api/v1/openai/files/${entry.file_id}/download`;
  }
  return null;
}

function isUrlCitation(cite: Annotation): cite is UrlCitation {
  return typeof (cite as { url?: unknown }).url === 'string';
}

function isContainerFileCitation(cite: Annotation): cite is ContainerFileCitation {
  const record = cite as { container_id?: unknown; file_id?: unknown };
  return typeof record.container_id === 'string' && typeof record.file_id === 'string';
}

function isFileCitation(cite: Annotation): cite is FileCitation {
  return typeof (cite as { file_id?: unknown }).file_id === 'string';
}

function injectFootnotes(text: string, citations: Annotation[]): FootnoteInjectionResult {
  if (!citations.length) {
    return { markdown: text, sources: [] };
  }

  const sorted = [...citations].sort((a, b) => (a.start_index ?? 0) - (b.start_index ?? 0));
  let output = text;
  let delta = 0;

  sorted.forEach((cite, idx) => {
    const label = idx + 1;
    const marker = `[^${label}]`;
    const insertAt = (cite.end_index ?? cite.start_index ?? 0) + delta;
    output = `${output.slice(0, insertAt)}${marker}${output.slice(insertAt)}`;
    delta += marker.length;
  });

  const sources = sorted.map((cite, idx) => {
    if (isUrlCitation(cite)) {
      return {
        label: String(idx + 1),
        title: cite.title,
        url: cite.url,
        filename: null,
        file_id: null,
        container_id: null,
      };
    }

    if (isContainerFileCitation(cite)) {
      const href = cite.url ?? buildDownloadHref({ file_id: cite.file_id, container_id: cite.container_id });
      return {
        label: String(idx + 1),
        title: cite.filename ?? `container file ${cite.file_id}`,
        url: href,
        filename: cite.filename ?? null,
        file_id: cite.file_id,
        container_id: cite.container_id,
      };
    }

    if (isFileCitation(cite)) {
      const href = buildDownloadHref({ file_id: cite.file_id });
      return {
        label: String(idx + 1),
        title: cite.filename ?? `file ${cite.file_id}`,
        url: href,
        filename: cite.filename ?? null,
        file_id: cite.file_id,
        container_id: null,
      };
    }

    return {
      label: String(idx + 1),
      title: 'Unknown citation',
      url: null,
      filename: null,
      file_id: null,
      container_id: null,
    };
  });

  const footnotes = sources
    .map((src) => {
      const href = src.url ?? buildDownloadHref(src) ?? '';
      return `[^${src.label}]: ${src.title ? `${src.title} — ` : ''}${href}`;
    })
    .join('\n');

  return { markdown: `${output}\n\n${footnotes}`, sources };
}

export const Response = memo(function Response({
  className,
  options,
  children,
  allowedImagePrefixes,
  allowedLinkPrefixes,
  defaultOrigin,
  parseIncompleteMarkdown: shouldParseIncompleteMarkdown = true,
  citations = null,
  ...props
}: ResponseProps) {
    let rawText: string | null = null;
    if (typeof children === 'string') {
      rawText = children;
    } else if (Array.isArray(children)) {
      const arr = children as unknown[];
      if (arr.length === 1 && typeof arr[0] === 'string') {
        rawText = arr[0] as string;
      }
    }

    const { markdown: withFootnotes, sources }: FootnoteInjectionResult =
      rawText && Array.isArray(citations) && citations.length
        ? injectFootnotes(rawText, citations)
        : { markdown: rawText ?? '', sources: [] };

    const baseContent = withFootnotes || children;
    const parsedChildren =
      typeof baseContent === 'string' && shouldParseIncompleteMarkdown
        ? parseIncompleteMarkdown(baseContent)
        : baseContent;
    const resolvedOrigin =
      defaultOrigin ?? (typeof window !== 'undefined' ? window.location.origin : '');

    return (
      <div
        className={cn(
          'size-full [&>*:first-child]:mt-0 [&>*:last-child]:mb-0',
          className
        )}
        {...props}
      >
        <HardenedMarkdown
          allowedImagePrefixes={allowedImagePrefixes ?? ['*']}
          allowedLinkPrefixes={allowedLinkPrefixes ?? ['*']}
          components={components}
          defaultOrigin={resolvedOrigin}
          rehypePlugins={[rehypeKatex]}
          remarkPlugins={[remarkGfm, remarkMath]}
          {...options}
        >
          {parsedChildren}
        </HardenedMarkdown>
        {sources.length ? (
          <Sources className="mt-3" defaultOpen={false}>
            <SourcesTrigger count={sources.length} />
            <SourcesContent>
              {sources.map((src) => {
                const href = src.url ?? buildDownloadHref(src) ?? undefined;
                const base = src.title ?? src.filename ?? src.url ?? 'source';
                const label = (() => {
                  if (href && src.url) {
                    try {
                      const host = new URL(src.url).hostname;
                      return `[${src.label}] ${base ?? host}`;
                    } catch {
                      return `[${src.label}] ${base}`;
                    }
                  }
                  return `[${src.label}] ${base}`;
                })();
                return href ? (
                  <Source key={src.label} href={href} title={label}>
                    <span className="text-xs font-medium">{label}</span>
                  </Source>
                ) : (
                  <div key={src.label} className="flex items-center gap-2 text-xs text-muted-foreground">
                    <span className="font-medium">[{src.label}]</span>
                    <span>{label}</span>
                  </div>
                );
              })}
            </SourcesContent>
          </Sources>
        ) : null}
      </div>
    );
  }
);

Response.displayName = 'Response';
