import React, { useEffect, useState } from 'react'

const ERROR_IMG_SRC =
  'data:image/svg+xml;base64,PHN2ZyB3aWR0aD0iODgiIGhlaWdodD0iODgiIHhtbG5zPSJodHRwOi8vd3d3LnczLm9yZy8yMDAwL3N2ZyIgc3Ryb2tlPSIjMDAwIiBzdHJva2UtbGluZWpvaW49InJvdW5kIiBvcGFjaXR5PSIuMyIgZmlsbD0ibm9uZSIgc3Ryb2tlLXdpZHRoPSIzLjciPjxyZWN0IHg9IjE2IiB5PSIxNiIgd2lkdGg9IjU2IiBoZWlnaHQ9IjU2IiByeD0iNiIvPjxwYXRoIGQ9Im0xNiA1OCAxNi0xOCAzMiAzMiIvPjxjaXJjbGUgY3g9IjUzIiBjeT0iMzUiIHI9IjciLz48L3N2Zz4KCg=='

const DEFAULT_FALLBACK_IMG_SRC =
  'data:image/svg+xml;base64,PHN2ZyB4bWxucz0iaHR0cDovL3d3dy53My5vcmcvMjAwMC9zdmciIHdpZHRoPSI4MDAiIGhlaWdodD0iNjAwIiB2aWV3Qm94PSIwIDAgODAwIDYwMCI+CiAgPGRlZnM+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9ImJnIiB4MT0iMCIgeTE9IjAiIHgyPSIxIiB5Mj0iMSI+CiAgICAgIDxzdG9wIG9mZnNldD0iMCIgc3RvcC1jb2xvcj0iI2ZmZTRmMCIvPgogICAgICA8c3RvcCBvZmZzZXQ9IjEiIHN0b3AtY29sb3I9IiNmNWRjZmYiLz4KICAgIDwvbGluZWFyR3JhZGllbnQ+CiAgICA8bGluZWFyR3JhZGllbnQgaWQ9InJpbmciIHgxPSIwIiB5MT0iMCIgeDI9IjEiIHkyPSIxIj4KICAgICAgPHN0b3Agb2Zmc2V0PSIwIiBzdG9wLWNvbG9yPSIjZmY1ZmEyIi8+CiAgICAgIDxzdG9wIG9mZnNldD0iMSIgc3RvcC1jb2xvcj0iI2ZmOTVkNSIvPgogICAgPC9saW5lYXJHcmFkaWVudD4KICAgIDxmaWx0ZXIgaWQ9InNoYWRvdyIgeD0iLTIwJSIgeT0iLTIwJSIgd2lkdGg9IjE0MCUiIGhlaWdodD0iMTQwJSI+CiAgICAgIDxmZURyb3BTaGFkb3cgZHg9IjAiIGR5PSI4IiBzdGREZXZpYXRpb249IjEyIiBmbG9vZC1jb2xvcj0iIzAwMCIgZmxvb2Qtb3BhY2l0eT0iMC4xNSIvPgogICAgPC9maWx0ZXI+CiAgPC9kZWZzPgogIDxyZWN0IHdpZHRoPSI4MDAiIGhlaWdodD0iNjAwIiBmaWxsPSJ1cmwoI2JnKSIvPgogIDxjaXJjbGUgY3g9IjQwMCIgY3k9IjI2MCIgcj0iMTQwIiBmaWxsPSIjZmZmZmZmY2MiIGZpbHRlcj0idXJsKCNzaGFkb3cpIi8+CiAgPGNpcmNsZSBjeD0iNDAwIiBjeT0iMjYwIiByPSIxMDUiIGZpbGw9Im5vbmUiIHN0cm9rZT0idXJsKCNyaW5nKSIgc3Ryb2tlLXdpZHRoPSIxNCIvPgogIDxjaXJjbGUgY3g9IjQwMCIgY3k9IjI2MCIgcj0iNjgiIGZpbGw9Im5vbmUiIHN0cm9rZT0iI2Q2MzM4NCIgc3Ryb2tlLXdpZHRoPSIxMCIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIi8+CiAgPHBhdGggZD0iTTMzMiAyNjBjMC0zOCAzMC02OCA2OC02OHM2OCAzMCA2OCA2OCIgZmlsbD0ibm9uZSIgc3Ryb2tlPSIjZDYzMzg0IiBzdHJva2Utd2lkdGg9IjEwIiBzdHJva2UtbGluZWNhcD0icm91bmQiLz4KICA8cGF0aCBkPSJNMzEwIDMxNmgxODAiIHN0cm9rZT0iI2Q2MzM4NCIgc3Ryb2tlLXdpZHRoPSIxMCIgc3Ryb2tlLWxpbmVjYXA9InJvdW5kIi8+CiAgPHRleHQgeD0iNDAwIiB5PSI0NDgiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtZmFtaWx5PSJJbnRlcixTZWdvZSBVSSxBcmlhbCxzYW5zLXNlcmlmIiBmb250LXNpemU9IjI4IiBmaWxsPSIjYTEwMDViIiBmb250LXdlaWdodD0iNzAwIj5TbWFydCBUcmF2ZWw8L3RleHQ+CiAgPHRleHQgeD0iNDAwIiB5PSI0ODIiIHRleHQtYW5jaG9yPSJtaWRkbGUiIGZvbnQtZmFtaWx5PSJJbnRlcixTZWdvZSBVSSxBcmlhbCxzYW5zLXNlcmlmIiBmb250LXNpemU9IjE2IiBmaWxsPSIjYTEwMDViIiBvcGFjaXR5PSIwLjkiPktow7RuZyBjw7Mg4bqjbmg8L3RleHQ+Cjwvc3ZnPg=='

type ImageWithFallbackProps = React.ImgHTMLAttributes<HTMLImageElement> & {
  fallbackSrc?: string
}

function normalizeSrc(src: React.ImgHTMLAttributes<HTMLImageElement>['src']): string | undefined {
  return typeof src === 'string' && src.trim().length > 0 ? src : undefined
}

export function ImageWithFallback(props: ImageWithFallbackProps) {
  const [didError, setDidError] = useState(false)
  const [didFallback, setDidFallback] = useState(false)

  const {
    src: srcProp,
    fallbackSrc = DEFAULT_FALLBACK_IMG_SRC,
    alt,
    style,
    className,
    ...rest
  } = props

  const normalizedSrc = normalizeSrc(srcProp)
  const normalizedFallback = normalizeSrc(fallbackSrc) ?? DEFAULT_FALLBACK_IMG_SRC

  const [currentSrc, setCurrentSrc] = useState<string | undefined>(normalizedSrc ?? normalizedFallback)

  useEffect(() => {
    setDidError(false)
    setDidFallback(false)
    setCurrentSrc(normalizedSrc ?? normalizedFallback)
  }, [normalizedSrc, normalizedFallback])

  const handleError = () => {
    if (!didFallback && currentSrc !== normalizedFallback) {
      setDidFallback(true)
      setCurrentSrc(normalizedFallback)
      return
    }
    setDidError(true)
  }

  return didError ? (
    <div
      className={`inline-block bg-gray-100 text-center align-middle ${className ?? ''}`}
      style={style}
    >
      <div className="flex items-center justify-center w-full h-full">
        <img
          src={ERROR_IMG_SRC}
          alt="Error loading image"
          {...rest}
          data-original-url={normalizedSrc}
        />
      </div>
    </div>
  ) : (
    <img
      src={currentSrc}
      alt={alt}
      className={className}
      style={style}
      {...rest}
      onError={handleError}
      data-original-url={normalizedSrc}
    />
  )
}
