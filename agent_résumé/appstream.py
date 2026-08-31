import streamlit as st
from agent import create_agent 
from transcrip import transcribe_audio
st.title("Agent Résumé")
st.audio_input("Téléchargez votre note vocale", key="audio_input")

if st.session_state.get("audio_input"):
    audio_file = st.session_state["audio_input"]
    try:
        transcription = transcribe_audio(audio_file, language="fr")
        st.session_state["transcription"] = transcription
        st.text_area("Transcription", value=transcription, height=200)
        if st.button("Générer le résumé"):
            with st.spinner("L'agent prépare le résumé..."):
                agent = create_agent()
                prompt_resume = f"""
                        Tu dois faire un résumé professionnel de cette réunion.

                        À partir de la transcription ci-dessous, produis :

                        1. Résumé court
                        2. Points importants
                        3. Décisions prises
                        4. Actions à faire
                        5. Questions ouvertes

                        N'invente rien. Si une information n'est pas présente, écris "Non précisé".

                        Transcription :
                        {transcription}
                        """
                resume = agent.run(prompt_resume)
                st.session_state["resume"] = resume
                if st.session_state.get("resume"):
                    st.subheader("Résumé généré")
                    st.markdown(st.session_state["resume"])
    except Exception as e:
        st.error(f"Erreur lors de la transcription : {str(e)}")
        
        
        
