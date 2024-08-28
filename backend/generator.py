# Instantiate a pre-trained Large Language Model from Azure OpenAI
#llm = AzureChatOpenAI(
#    deployment_name="gpt-4o",
#    api_version="2023-06-01-preview"
#)
#
#
#
#system_prompt = (
#    "You are an assistant for question-answering tasks."
#    "Use the following pieces of retrieved context to answer the question." 
#    "If you don't know the answer, say that you don't know." 
#    "Use three sentences maximum and keep the answer concise."
#    "\n\n"
#    "{context}"
#)
#
#prompt = ChatPromptTemplate.from_messages(
#    [
#        ("system", system_prompt),
#        ("human", "{question}"),
#    ]
#)
#
#parser = StrOutputParser()
#
#rag_chain = (
#    {"context": retriever | format_docs, "question": RunnablePassthrough()}
#    | prompt
#    | llm
#    | parser
#)