export type ImmichImage = {
  immich_asset_id: string
  original_file_name: string
  file_created_at: string | null
  width: number | null
  height: number | null
  is_favorite: boolean
  thumbnail_url: string
}

export type ImmichImagePage = {
  items: ImmichImage[]
  total: number
  page: number
  page_size: number
  pages: number
}

export type ImmichAlbum = {
  immich_album_id: string
  album_name: string
  asset_count: number
  thumbnail_asset_id: string | null
  thumbnail_url: string | null
  start_date: string | null
  end_date: string | null
}

export type ImmichAlbumList = {
  items: ImmichAlbum[]
}

export type ImmichAssetLink = ImmichImage & {
  id: string
  asset_id: string
  created_at: string
  updated_at: string
}

export type ImmichAssetLinkList = {
  items: ImmichAssetLink[]
}

export type ImmichImageQuery = {
  page?: number
  page_size?: number
  search?: string
  album_id?: string
  favorite_only?: boolean
  taken_after?: string
  taken_before?: string
}
