# UNIMAP building-image storage setup

## Bucket name
Create a **PUBLIC** bucket in Supabase Storage named exactly:

`unimap-building-media`

Use this exact name in Render as `SUPABASE_S3_BUILDINGS_BUCKET`. Public access is required by the current `SupabaseBaseStorage.url()` implementation, which returns public object URLs. Do not put credentials in source code or commit `.env`.

## Supabase configuration
The backend reuses the existing S3-compatible credentials already configured for profile/news uploads:
- `SUPABASE_S3_ENDPOINT`
- `SUPABASE_S3_REGION`
- `SUPABASE_S3_ACCESS_KEY_ID`
- `SUPABASE_S3_SECRET_ACCESS_KEY`
- `SUPABASE_PUBLIC_STORAGE_URL` is already set in settings

Add `SUPABASE_S3_BUILDINGS_BUCKET=unimap-building-media` to Render Environment. Use the same S3 credentials as the working profile/news storage. In Supabase, ensure the S3 credentials have permission to upload objects to this bucket. The bucket must be public for unauthenticated image display; do not store private user files in this bucket.

## Deploy steps
1. Create the bucket before deploying.
2. Add the environment variable in Render.
3. Deploy this code. The build command's `python manage.py migrate` will apply migration `campus.0016_building_images_supabase_storage`. This migration changes Django field storage configuration; it does not delete database rows or upload existing local files.
4. Test an upload through the actual building create/edit form. Confirm the response contains a public Supabase URL and the image loads after refresh.

## Existing image files
Changing storage does not automatically migrate existing building photos/icons. Existing records may contain local file paths; those files need a separate upload/migration if they must remain visible. Keep a backup before any bulk media migration.

## Troubleshooting
- `NoSuchBucket`: bucket name or region/endpoint mismatch.
- `AccessDenied`: S3 credentials lack permission or bucket policy/configuration is wrong.
- Upload succeeds but image 404s: confirm the bucket is public and the public URL path is correct.
- Profile uploads still return “not a valid image”: that is a separate request/serializer issue; test it independently from building storage.
