import React, {useState} from "react";
import {Input} from "antd";
import {AudioOutlined, EnterOutlined, PaperClipOutlined} from "@ant-design/icons";
import styles from "./styles.module.scss";

const ChatWidget = () => {
	const [text, setText] = useState("");

	return (
		<div className={styles.container}>
			<Input placeholder='Текст писать сюда' value={text} onChange={e => setText(e.target.value)} className={styles.input} />
			<PaperClipOutlined className={styles.icon} />
			<AudioOutlined className={styles.icon} />
			<EnterOutlined className={styles.icon} />
		</div>
	);
};

export default ChatWidget;
