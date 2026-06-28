from PIL import Image
from PIL.ExifTags import TAGS, GPSTAGS


def parse_image(filepath):
    structured_data = {}
    
    img = Image.open(filepath)
    exif = img._getexif() if hasattr(img, '_getexif') else None
    
    if exif:
        exif_data = {}
        for tag_id, value in exif.items():
            tag = TAGS.get(tag_id, tag_id)
            exif_data[tag] = value
        
        # Extract timestamp
        for key in ['DateTime', 'DateTimeOriginal', 'DateTimeDigitized']:
            if key in exif_data:
                structured_data['timestamp'] = exif_data[key]
                break
        
        # Extract camera make
        if 'Make' in exif_data:
            structured_data['camera_make'] = exif_data['Make']
        
        # Extract camera model
        if 'Model' in exif_data:
            structured_data['camera_model'] = exif_data['Model']
        
        # Extract GPS coordinates
        gps_ifd = exif_data.get('GPSInfo', {})
        if gps_ifd:
            gps_data = {}
            for tag_id, value in gps_ifd.items():
                tag = GPSTAGS.get(tag_id, tag_id)
                gps_data[tag] = value
            
            # GPS Latitude
            lat = gps_data.get('GPSLatitude')
            lat_ref = gps_data.get('GPSLatitudeRef')
            if lat and lat_ref:
                structured_data['gps_latitude'] = _convert_dms_to_decimal(lat, lat_ref)
            
            # GPS Longitude
            lon = gps_data.get('GPSLongitude')
            lon_ref = gps_data.get('GPSLongitudeRef')
            if lon and lon_ref:
                structured_data['gps_longitude'] = _convert_dms_to_decimal(lon, lon_ref)
            
            # GPS Altitude
            altitude = gps_data.get('GPSAltitude')
            if altitude is not None:
                if isinstance(altitude, tuple):
                    altitude = altitude[0] / altitude[1] if altitude[1] != 0 else 0
                alt_ref = gps_data.get('GPSAltitudeRef', 0)
                structured_data['gps_altitude'] = float(altitude) if not alt_ref else -float(altitude)
    
    return structured_data


def _convert_dms_to_decimal(dms, ref):
    degrees = float(dms[0][0]) / dms[0][1] if isinstance(dms[0], tuple) else float(dms[0])
    minutes = float(dms[1][0]) / dms[1][1] if isinstance(dms[1], tuple) else float(dms[1])
    seconds = float(dms[2][0]) / dms[2][1] if isinstance(dms[2], tuple) else float(dms[2])
    
    decimal = degrees + (minutes / 60.0) + (seconds / 3600.0)
    
    if ref in ['S', 'W']:
        decimal = -decimal
    
    return round(decimal, 6)