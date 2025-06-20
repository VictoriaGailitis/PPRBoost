import React, {useState} from "react";

import styles from "./styles.module.scss";
import Dragger from "antd/es/upload/Dragger";
import {InboxOutlined, LinkOutlined} from "@ant-design/icons";
import {Input} from "antd";
import {API_URL} from "../../shared/consts";

const AttachPopup = ({files, setFiles}) => {
	const [input, setIput] = useState("");

	const props = {
		name: "file",
		multiple: true,
		action: `${API_URL}/upload_file`,
		accept: ".pdf, .doc, .docx, .pptx, .csv, .xls, .xlsx, .html, .htm, .md, .xml, .json, .mp3, .jpg, .png",
		maxCount: 3,
		onChange(info) {
			const {response, file} = info;
			const {status} = info.file;
			if (status === "done") {
				const fileUrl = response?.url || file.url;
				setFiles(prev => [...prev, fileUrl]);
			}
		},
	};

	return (
		<div className={styles.attachPopup}>
			<div className={styles.title}>Загрузка файла</div>
			<Dragger {...props}>
				<p className='ant-upload-drag-icon'>
					<InboxOutlined />
				</p>
				<p className='ant-upload-text'>Нажмите или перенесите файл в эту область</p>
				<p className='ant-upload-hint'>Одновременно можно загрузить до 3 файлов</p>
			</Dragger>
			{files.length > 0 &&
				files.map(file => (
					<div className={styles.linkedFiles}>
						<LinkOutlined />
						{file}
					</div>
				))}
			<div className={styles.title}>Ссылка на ресурс</div>
			<Input value={input} onChange={e => setIput(e.target.value)} placeholder='Введите ссылку' />
		</div>
	);
};

export default AttachPopup;
