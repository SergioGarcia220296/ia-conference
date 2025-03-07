import json
import boto3
import time
############
#  FASE 1  #
############

# Configurar cliente de Transcribe
transcribe = boto3.client('transcribe', region_name='us-west-2')

# Nombre del trabajo de transcripción
job_name = "demo-transcription"
audio_uri = "s3://qubika-conference/transcribe/exercise.mp3"

# Iniciar transcripción
transcribe.delete_transcription_job( TranscriptionJobName=job_name )
transcribe.start_transcription_job(
    TranscriptionJobName=job_name,
    Media={'MediaFileUri': audio_uri},
    MediaFormat='mp3',
    OutputBucketName='qubika-conference',
    OutputKey='output/',
    LanguageCode='es-US'
)

# Esperar a que termine
while True:
    status = transcribe.get_transcription_job(TranscriptionJobName=job_name)
    if status['TranscriptionJob']['TranscriptionJobStatus'] in ['COMPLETED', 'FAILED']:
        break
    print("Transcribiendo...")
    time.sleep(5)
############
#  FASE 2  #
############

# Configurar clientes de S3 y Bedrock
s3 = boto3.client('s3')
bedrock = boto3.client('bedrock-runtime', region_name='us-west-2')

# Obtener el archivo transcrito desde el bucket
bucket_name = "qubika-conference"
file_key = "output/demo-transcription.json"

# Descarga el archivo de Transcribe desde S3 y extrae el texto transcrito.
response = s3.get_object(Bucket=bucket_name, Key=file_key)
data = json.loads(response['Body'].read().decode('utf-8'))

# Obtener el texto transcrito
transcription_text = data['results']['transcripts'][0]['transcript']
print("Texto Transcrito del audio en S3\n\n" + transcription_text)

# Envia el texto transcrito a AWS Bedrock
prompt = f"\n\nHuman: {transcription_text}\n\nAssistant:"

payload = {
    "messages": [
        {"role": "user", "content": transcription_text}
    ],
    "max_tokens": 500,
    "anthropic_version" : "bedrock-2023-05-31"
}

response = bedrock.invoke_model(
        modelId="us.anthropic.claude-3-7-sonnet-20250219-v1:0",
        body=json.dumps(payload),
        contentType="application/json",
        accept="application/json"
    )

# Convertir la respuesta JSON a un diccionario de Python
response_body = json.loads(response["body"].read())

# Extraer el texto de la respuesta de Claude 3
assistant_response = response_body["content"][0]["text"]
print("Respuesta desde AWS Bedrock con Claude\n\n" + assistant_response)

############
#  FASE 3  #
############

# Convertir texto a voz con Amazon Polly

# Configurar cliente de Polly
polly = boto3.client('polly', region_name='us-west-2')

# Generar audio a partir del texto
response_polly = polly.start_speech_synthesis_task(
    Text=assistant_response,
    OutputS3BucketName='qubika-conference',
    OutputS3KeyPrefix='polly/',
    OutputFormat='mp3',
    VoiceId='Lucia'
)

print("Respuesta convertida a voz. Guardada en S3")

