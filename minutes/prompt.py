from langchain.prompts import PromptTemplate

summary_system_content = "You are a helpful assistant."
# summary_user_content = "Create a structured summary of the meeting transcript provided using markdown format written in the original language. Organize the summary into distinct topics and ensure all explicitly mentioned information is included in concise sentences. Example topics: ['Introduction','[Item1, Item2, Item3...]','Action items','Conclusion']. Note that any topics not discussed in the transcript should not be included in the summary. Additionally, refrain from documenting that was not mentioned in the transcript. Transcript: '{transcript}', Language:'{org_lang}'."
summary_user_content = PromptTemplate(
    input_variables=["user_prompt","transcript","org_lang"],
    template="Create a structured summary of the transcript provided using markdown format written in the original language. Organize the summary into distinct topics and ensure all explicitly mentioned information is included in concise sentences. Note that any topics not described in the transcript should not be included in the summary. Additionally, refrain from documenting that was not mentioned in the transcript. {user_prompt}. Transcript: '{transcript}', Language:'{org_lang}'."
    )

summary_chunks_user_content = "Create and update a structured summary of the transcript provided using markdown format written in the original language. Organize the summary into distinct topics and ensure all explicitly mentioned information is included in concise sentences. Note that any topics not discussed in the transcript should not be included in the summary. Additionally, refrain from documenting that was not described in the transcript.  {user_prompt}. A chunk of transcripts is passed in a row. So, update the previously created summary by current transcript index: {i}. Transcript ({i}/{total}): '{transcript}', '{summary}', Language:'{org_lang}'."

translation_system_content = "You are a helpful translator."
translation_user_content = "Create a translated version for the '{summary}' using markdown format in '{lang}' language . Maintain the same topic structure and content."
chat_detect_lang_content = "What is the ISO-639-1 language code for the language used in the provided text? text:'{text}'"
continue_content = "Continue generating text while taking into account the token limit constraints for Chat GPT."

summary_template = """Write a concise summary of the following:

{text}

Organize the summary into distinct topics and ensure all explicitly mentioned information is included in CONCISE SUMMARY IN {org_lang} BY MARKDOWN FORMAT.  :"""
refine_template = (
    "Your job is to produce a final summary by Markdown format\n"
    "We have provided an existing summary up to a certain point: {existing_answer}\n"
    "We have the opportunity to refine the existing summary"
    "(only if needed) with some more context below.\n"
    "------------\n"
    "{text}\n"
    "------------\n"
    "Given the new context, refine the original summary Organize the summary into distinct topics and ensure all explicitly mentioned information is included in CONCISE SUMMARY BY MARKDOWN FORMAT. "
    "If the context isn't useful, return the original summary."
)