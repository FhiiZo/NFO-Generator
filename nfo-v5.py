import os
import re
import requests
from pymediainfo import MediaInfo

# Clé API TMDb
TMDB_API_KEY = "cab621e2bbe649631974b2ddf2452a5b"

# Dictionnaire des langues
LANGUAGES = {
        "en": "Anglais",
        "fr": "Français",
        "es": "Espagnol",
        "de": "Allemand",
        "it": "Italien",
        "ja": "Japonais",
        "ru": "Russe",
        "zh": "Chinois",
        "ko": "Coréen",
        "pt": "Portugais",
        "ar": "Arabe",
        # Ajouter d'autres langues si nécessaire
        }

def search_tmdb(movie_name):
    """
    Recherche le film sur TMDb et retourne l'URL de la page correspondante.
    :param movie_name: Nom du film
    :return: URL de TMDb ou 'Inconnu' si aucun résultat trouvé
    """
    try:
        url = f"https://api.themoviedb.org/3/search/movie"
        params = {
                "api_key": TMDB_API_KEY,
                "query": movie_name,
                "language": "fr",
                }
        response = requests.get(url, params=params)
        response.raise_for_status()
        results = response.json().get("results", [])
        if results:
            movie_id = results[0]["id"]
            return f"https://www.themoviedb.org/movie/{movie_id}"
        return "Inconnu"
    except Exception as e:
        print(f"Erreur lors de la recherche TMDb pour '{movie_name}': {e}")
        return "Inconnu"

def detect_source_and_zone(file_name):
    sources = {
            "NF": "Netflix",
            "AMZN": "Amazon Prime Vidéo",
            "MAX": "HBO Max",
            "HMAX": "HBO Max",
            "DSNP": "Disney+",
            "HULU": "Hulu",
            "APPLTV": "Apple TV+",
            "ATVP": "Apple TV+",
            "PCOK": "Peacock",
            "iT": "iTunes",
            "CNLP": "Canal+",
            "PMTP": "Paramount+",
            "PRIME": "Amazon Prime Vidéo",
            }

    detected_source = None
    for key, value in sources.items():
        if key in file_name.upper():
            detected_source = value
            break

    source_suffix = ""
    file_name_upper = file_name.upper()
    if detected_source:
        if "BLURAY" in file_name_upper or "BLU-RAY" in file_name_upper:
            if any(word in file_name_upper for word in ["FRENCH", "CA"]):
                source_suffix = "Zone A"
            elif any(word in file_name_upper for word in ["TRUEFRENCH", "VOF", "VFF", "VFi"]):
                source_suffix = "Zone B"

    if detected_source:
        return f"{detected_source} {source_suffix}".strip()
    return "Inconnu"

def extract_movie_name(file_name):
    file_name_cleaned = os.path.splitext(file_name)[0]
    # Utiliser une expression régulière pour trouver tout ce qui est avant l'année (par exemple, 2022, 2023, etc.)
    match = re.match(r"^(.*?)(?:\.|\s)(19\d{2}|20\d{2})", file_name_cleaned)
    if match:
        movie_name = match.group(1)
    else:
        movie_name = file_name_cleaned

    # Supprimer les mots-clés non pertinents
    movie_name = " ".join(part for part in movie_name.split(".") if not any(keyword in part.lower() for keyword in [
        "1080p", "720p", "bluray", "web", "hdrip", "dvdrip", "x264", "x265", "h264", "h265", "remux"
        ]))
    return movie_name.strip()

def generate_nfo(file_path):
    """
    Génère un fichier .nfo formaté en français avec les informations extraites via MediaInfo et TMDb.
    :param file_path: Chemin complet vers le fichier vidéo
    """
    try:
        media_info = MediaInfo.parse(file_path)
        nfo_content = [
                """
d8888b. d88888b d8888b. d888888b d8888b. d888888b db   db
88  `8D 88'     88  `8D   `88'   88  `8D `~~88~~' 88   88
88oobY' 88ooooo 88oooY'    88    88oobY'    88    88ooo88
88`8b   88~~~~~ 88~~~b.    88    88`8b      88    88~~~88
88 `88. 88.     88   8D   .88.   88 `88.    88    88   88
88   YD Y88888P Y8888P' Y888888P 88   YD    YP    YP   YP
---------------------------------------------------------- 
|                     Présente                           |
----------------------------------------------------------
                """
                ]

        # Nom du fichier et détection du film
        file_name = os.path.basename(file_path)
        movie_name = extract_movie_name(file_name)
        tmdb_url = search_tmdb(movie_name)
        source = detect_source_and_zone(file_name)

        nfo_content.append(f"{file_name}")

        # Informations générales
        general_info = next((t for t in media_info.tracks if t.track_type == "General"), None)
        if general_info:
            nfo_content.append("\nINFORMATIONS GÉNÉRALES")
            nfo_content.append(f"FORMAT                  : {general_info.format}")
            nfo_content.append(f"TAILLE                  : {general_info.other_file_size[0] if general_info.other_file_size else 'Inconnu'}")
            nfo_content.append(f"DURÉE                   : {general_info.other_duration[0] if general_info.other_duration else 'Inconnu'}")
            nfo_content.append(f"TMDB                    : {tmdb_url}")
            nfo_content.append(f"SOURCE                  : {source}\n")

        # Vidéo
        video_info = next((t for t in media_info.tracks if t.track_type == "Video"), None)
        if video_info:
            nfo_content.append("VIDÉO")
            nfo_content.append(f"CODEC                   : {video_info.format}")

            resolution = "Inconnue"
            additional_type = ""
            if video_info.width and video_info.height:
                width = int(video_info.width)
                height = int(video_info.height)
                if width == 1920 and height == 1080:
                    resolution = "1080p"
                elif width == 1280 and height == 720:
                    resolution = "720p"
                elif width == 3840 and height == 2160:
                    resolution = "2160p"

                if video_info.display_aspect_ratio:
                    aspect_ratio = float(video_info.display_aspect_ratio)
                    if aspect_ratio == 1.90 and width >= 1920:
                        additional_type = "IMAX"
                    elif aspect_ratio == 1.78:
                        additional_type = "Open Matte"
                    elif aspect_ratio == 2.39:
                        additional_type = "Cinémascope"

        video_type = f"{resolution} {additional_type}".strip()
        nfo_content.append(f"TYPE                    : {video_type}")
        nfo_content.append(f"FRÉQUENCE D'IMAGE       : {video_info.frame_rate} fps")
        nfo_content.append(f"ASPECT RATIO            : {video_info.display_aspect_ratio}")
        nfo_content.append(f"PROFONDEUR DE BITS      : {video_info.bit_depth} bits")
        nfo_content.append(f"PROFIL FORMAT           : {video_info.format_profile or 'Inconnu'}")
        nfo_content.append(f"DÉBIT                   : {video_info.other_bit_rate[0] if video_info.other_bit_rate else 'Inconnu'}")
        nfo_content.append(f"DIMENSIONS (L x H)      : {video_info.width} x {video_info.height} pixels\n")

        # Audio
        audio_tracks = [t for t in media_info.tracks if t.track_type == "Audio"]
        if audio_tracks:
            nfo_content.append("AUDIO")
            for i, audio in enumerate(audio_tracks, start=1):
                nfo_content.append(f"PISTE {i}")
                nfo_content.append(f"CODEC                   : {audio.format}")
                language_full = LANGUAGES.get(audio.language, audio.language) if audio.language else "Inconnue"
                nfo_content.append(f"LANGUE                  : {language_full}")
                nfo_content.append(f"CANAL                   : {audio.channel_s}")
                nfo_content.append(f"DÉBIT                   : {audio.other_bit_rate[0] if audio.other_bit_rate else 'Inconnu'}")
                nfo_content.append(f"TAUX D'ÉCHANTILLON      : {audio.other_sampling_rate[0] if audio.other_sampling_rate else 'Inconnu'}")
                nfo_content.append(f"AUTRES INFORMATIONS     : {audio.other_compression_mode[0] if audio.other_compression_mode else 'Inconnu'}\n")

        # Sous-titres (gère plusieurs pistes et détecte FORCED / FULL)
        subtitle_tracks = [t for t in media_info.tracks if t.track_type == "Text"]
        if subtitle_tracks:
            nfo_content.append("SOUS-TITRES")
            for idx, sub in enumerate(subtitle_tracks, 1):
                language_full = LANGUAGES.get(sub.language, sub.language) if sub.language else "Inconnu"
                forced = "FORCED" if sub.forced == "Yes" else ""
                full = "FULL" if sub.text_description and "full" in sub.text_description.lower() else ""
                details = f"({forced} {full})" if forced or full else ""
                nfo_content.append(f"Piste {idx} : {language_full} {details}".strip())
            nfo_content.append("")

        # Ajout des notes de release
        nfo_content.append("\nNOTES DE RELEASE")
        nfo_content.append("S'il y'a une note a ajouter sur la rls faites la ici, sinon ecrire NEANT.\n")

        # Section REMERCIEMENT et NOTES DU GROUPE
        nfo_content.append("\nREMERCIEMENT")
        nfo_content.append("Un grand merci à nos Encodeurs / Uploadeurs qui font un travail incroyable.")
        nfo_content.append("Ils donnent de leurs temps pour faire des Releases de qualité.")

        # Ajout des notes de groupe
        nfo_content.append("NOTES DU GROUPE")
        nfo_content.append("Merci de ne pas modifier nos releases lors de leur upload ailleurs.")
        nfo_content.append("Gardez le NFO intact et conservez les noms de fichiers inchangés.")

        # Enregistrement du fichier NFO
        nfo_name = os.path.splitext(file_path)[0] + ".nfo"
        with open(nfo_name, "w", encoding="utf-8") as nfo_file:
            nfo_file.write("\n".join(nfo_content))

        print(f"Fichier NFO créé : {nfo_name}")

    except Exception as e:
        print(f"Erreur lors du traitement du fichier {file_path}: {e}")

def process_directory(directory_path):
    """
    Parcourt un répertoire pour créer des fichiers .nfo pour chaque fichier vidéo trouvé.
    :param directory_path: Chemin du répertoire
    """
    supported_extensions = [".mp4", ".mkv"]
    for root, _, files in os.walk(directory_path):
        for file in files:
            if any(file.lower().endswith(ext) for ext in supported_extensions):
                file_path = os.path.join(root, file)
                generate_nfo(file_path)

if __name__ == "__main__":
    directory = input("Entrez le chemin du répertoire à analyser : ").strip()
    if os.path.isdir(directory):
        process_directory(directory)
    else:
        print("Chemin de répertoire invalide.")
