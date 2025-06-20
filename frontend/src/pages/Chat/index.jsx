import React, {useState, useRef, useEffect} from "react";
import {useDispatch, useSelector} from "react-redux";
import SpeechRecognition, {useSpeechRecognition} from "react-speech-recognition";
import styles from "./styles.module.scss";
import Message from "../../components/Message";
import {toogleOverlay} from "../../app/slices/Layout";
import classNames from "classnames";
import {Button, Modal} from "antd";
import {useNavigate, useParams, useSearchParams} from "react-router-dom";
import {addMessage, attachStreaming, createChat, getCurrentChat, postCategory, streamingChat} from "../../app/slices/List";
import {BulbOutlined} from "@ant-design/icons";
import AttachPopup from "../../components/AttachPopup/AttachPopup";

const Chat = () => {
	const dispatch = useDispatch();

	const {id} = useParams();
	const messages = useSelector(s => s.list.activeChat);
	const [searchParams] = useSearchParams();
	const isNew = searchParams.get("isNew") === "true";
	const [popup, setPopup] = useState(false);
	const [files, setFiles] = useState([]);
	const navigate = useNavigate();
	const overlay = useSelector(state => state.layout.overlay);
	const [reson, setReson] = useState(false);
	const [input, setInput] = useState("");
	const messagesEndRef = useRef();
	const textareaRef = useRef();
	const isStreamingPending = useSelector(state => state.list.isStreamingPending);

	console.log(files);

	const {transcript, listening, resetTranscript, browserSupportsSpeechRecognition} = useSpeechRecognition();

	useEffect(() => {
		if (id && !isNew) {
			dispatch(getCurrentChat(id));
		}
	}, [id, dispatch, isNew]);

	useEffect(() => {
		if (transcript) {
			setInput(transcript);
		}
	}, [transcript]);

	useEffect(() => {
		adjustTextareaHeight();
	}, [input]);

	const handleSubmit = async e => {
		e.preventDefault();
		if (!input) return;

		if (!id) {
			const result = await dispatch(createChat({title: input}));
			dispatch(postCategory({chat_id: result.payload.id, text: input}));
			if (files.length > 0) {
				dispatch(attachStreaming({attachments: files, chatId: result.payload.id, message: input, reasoning: reson}));
			} else {
				dispatch(streamingChat({message: input, reasoning: reson, chat_id: result.payload.id}));
			}
			navigate(`/${result.payload.id}?isNew=true`);
		} else {
			dispatch(addMessage({chat_id: Number(id), content: input, role: "user", created_at: new Date().toLocaleString()}));
			dispatch(postCategory({chat_id: Number(id), text: input}));
			if (files.length > 0) {
				dispatch(attachStreaming({attachments: files, chatId: Number(id), reasoning: reson, message: input}));
			} else {
				dispatch(streamingChat({message: input, reasoning: reson, chat_id: Number(id)}));
			}
		}
		setInput("");
		resetTranscript();
	};

	const startListening = () => {
		resetTranscript();
		SpeechRecognition.startListening({language: "ru-RU"});
	};

	if (!browserSupportsSpeechRecognition) {
		return <span>Ваш браузер не поддерживает speech recognition.</span>;
	}

	const adjustTextareaHeight = () => {
		if (textareaRef.current) {
			textareaRef.current.style.height = "auto";
			textareaRef.current.style.height = `${textareaRef.current.scrollHeight}px`;
		}
	};

	return (
		<>
			<div className={styles.chat}>
				<div className={styles.mobileTitle}>
					<div className={classNames(styles.arrow, overlay && styles.active)} onClick={() => dispatch(toogleOverlay())}></div>
					<div>{}</div>
				</div>
				<div className={styles.messages}>
					{!!messages?.messages?.length && messages.messages.map((msg, i) => <Message key={msg.id} message={msg} isBotMessage={(i + 1) % 2 === 0} />)}
					{isStreamingPending && <Message isStreamingPending />}
					<div ref={messagesEndRef} />
				</div>

				<form onSubmit={handleSubmit} className={styles.form}>
					<div className={styles.inputCont}>
						<textarea ref={textareaRef} value={input} onChange={e => setInput(e.target.value)} placeholder='Введите сообщение...' className={styles.realInput} rows={1} />
						<div className={styles.inputBot}>
							<div className={styles.rightInput}>
								<div className={styles.attach} onClick={() => setPopup(true)}></div>
								<Button className={styles.reson} onClick={() => setReson(prev => !prev)} type={reson ? "primary" : undefined}>
									<BulbOutlined />
									Рассуждение
								</Button>
							</div>

							<div className={styles.rightInput}>
								<button type='button' onClick={listening ? SpeechRecognition.stopListening : startListening} title={listening ? "Остановить запись" : "Начать запись"} className={styles.mic}></button>
								<button type='submit' className={styles.send}></button>
							</div>
						</div>
					</div>
				</form>
			</div>
			<Modal visible={popup} okText={"Прикрепить"} cancelButtonProps={{style: {display: "none"}}} onCancel={() => setPopup(false)}>
				<AttachPopup setFiles={setFiles} setPopup={setPopup} files={files} />
			</Modal>
		</>
	);
};

export default Chat;
