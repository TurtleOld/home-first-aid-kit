import { describe, it, expect, vi, afterEach } from 'vitest'
import { compressImageFile } from './image'

function makeFile({ name = 'photo.png', type = 'image/png', size = 1000 } = {}) {
  const file = new File([new Uint8Array(size)], name, { type })
  return file
}

describe('compressImageFile', () => {
  afterEach(() => {
    vi.unstubAllGlobals()
  })

  it('returns the original file for non-image types', async () => {
    const file = makeFile({ name: 'doc.pdf', type: 'application/pdf' })
    await expect(compressImageFile(file)).resolves.toBe(file)
  })

  it('returns the original file for SVG images', async () => {
    const file = makeFile({ name: 'icon.svg', type: 'image/svg+xml' })
    await expect(compressImageFile(file)).resolves.toBe(file)
  })

  it('returns the original file when compression fails', async () => {
    vi.stubGlobal('createImageBitmap', vi.fn().mockRejectedValue(new Error('decode error')))

    const file = makeFile()
    await expect(compressImageFile(file)).resolves.toBe(file)
  })

  it('returns a smaller JPEG when the compressed blob is smaller', async () => {
    vi.stubGlobal('createImageBitmap', vi.fn().mockResolvedValue({ width: 3200, height: 1600 }))

    const toBlobMock = vi.fn((callback) => {
      callback(new Blob([new Uint8Array(10)], { type: 'image/jpeg' }))
    })
    const getContextMock = vi.fn(() => ({ drawImage: vi.fn() }))

    vi.stubGlobal('document', {
      ...globalThis.document,
      createElement: vi.fn(() => ({
        width: 0,
        height: 0,
        getContext: getContextMock,
        toBlob: toBlobMock
      }))
    })

    const file = makeFile({ size: 1000 })
    const result = await compressImageFile(file)

    expect(result).toBeInstanceOf(File)
    expect(result.name).toBe('photo.jpg')
    expect(result.type).toBe('image/jpeg')
    expect(result.size).toBeLessThan(file.size)
  })

  it('returns the original file when the compressed blob is not smaller', async () => {
    vi.stubGlobal('createImageBitmap', vi.fn().mockResolvedValue({ width: 100, height: 100 }))

    const toBlobMock = vi.fn((callback) => {
      callback(new Blob([new Uint8Array(2000)], { type: 'image/jpeg' }))
    })
    const getContextMock = vi.fn(() => ({ drawImage: vi.fn() }))

    vi.stubGlobal('document', {
      ...globalThis.document,
      createElement: vi.fn(() => ({
        width: 0,
        height: 0,
        getContext: getContextMock,
        toBlob: toBlobMock
      }))
    })

    const file = makeFile({ size: 1000 })
    await expect(compressImageFile(file)).resolves.toBe(file)
  })
})
