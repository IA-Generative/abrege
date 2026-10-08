// Short error codes set by the worker (numeric, see server/src/utils/error_codes.py: 1xx model, 2xx internal api, 3xx input/ocr, 999 unknown). The UI shows the code
// and a one-line, non-technical hint in a tooltip; the full cause is in the worker logs.
const MESSAGES: Record<number, string> = {
  101: 'Le modèle a mis trop de temps à répondre.',
  102: 'Le modèle est momentanément indisponible.',
  103: 'Trop de requêtes vers le modèle, réessayez plus tard.',
  104: 'Accès au modèle refusé (configuration).',
  105: 'Le texte est trop long pour le modèle.',
  106: 'Le modèle a refusé la requête.',
  107: 'La réponse du modèle est inexploitable.',
  201: 'Enregistrement des résultats impossible (service injoignable).',
  202: 'Enregistrement des résultats refusé par le service.',
  301: 'L\'extraction du texte (OCR) a échoué.',
  302: 'Le contenu de l\'URL n\'a pas pu être récupéré.',
  303: 'Ce type de contenu n\'est pas pris en charge.',
  304: 'Aucun contenu à traiter.',
  999: 'Erreur inattendue.',
}

/** Tooltip text for an error code: the hint plus the code to quote when asking for help. */
export function describeError (code?: number | null): string | undefined {
  if (code == null) { return undefined }
  return `${MESSAGES[code] ?? MESSAGES[999]} (code ${code})`
}
