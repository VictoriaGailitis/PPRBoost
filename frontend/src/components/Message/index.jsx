import React, {useEffect, useState} from "react";
import styles from "./styles.module.scss";
import ClassNames from "classnames";
import {DownOutlined, FrownOutlined, LinkOutlined, MehOutlined, SmileOutlined} from "@ant-design/icons";
import {useDispatch, useSelector} from "react-redux";
import {Rate, Spin} from "antd";
import {rateMessage} from "../../app/slices/Chat";
import ReactMarkdown from "react-markdown";
import classNames from "classnames";
import {API_URL} from "../../shared/consts";

const customIcons = {
	1: <FrownOutlined size={25} />,
	2: <FrownOutlined />,
	3: <MehOutlined />,
	4: <SmileOutlined />,
	5: <SmileOutlined />,
};

const Message = ({isStreamingPending, message = null, isBotMessage = false}) => {
	const [rate, setRate] = useState(message?.rating);
	const [showSource, setShowSource] = useState(false);
	const dispatch = useDispatch();
	const [displayedText, setDisplayedText] = useState("");

	useEffect(() => {
		if (isBotMessage && message && message.text) {
			let index = 0;
			const interval = setInterval(() => {
				setDisplayedText(prevText => prevText + message.text[index]);
				index++;

				if (index === message.text.length) {
					clearInterval(interval);
					// Проверяем, если текст заканчивается на 'undefined' и удаляем его
					setDisplayedText(prevText => prevText.replace(/undefined$/, ""));
				}
			}, 10);

			return () => clearInterval(interval);
		}
	}, [message, isBotMessage]);

	const onChange = value => {
		setRate(value);
		dispatch(rateMessage({id: message?.id, rating: value}));
	};

	return (
		<div className={ClassNames(styles.message, (isBotMessage || isStreamingPending) && styles.botMessage)}>
			<div className={styles.messageCont}>
				<div className={styles.msgText}>
					{message ?
						<>
							<div>
								<ReactMarkdown>{displayedText || message.content}</ReactMarkdown>
								{message.sources && (
									<div className={styles.sources}>
										<div onClick={() => setShowSource(!showSource)}>
											Источники
											<DownOutlined className={classNames(styles.dropdown, showSource && styles.rotate)} />
										</div>
										{showSource &&
											message.sources.map((item, index) => {
												const fileName = item.source.replace("/content/", "").replace(/_/g, " ");
												const url = `${API_URL}${item.source}#${item.page}`;

												return (
													<div className={styles.sourceItem} key={index}>
														<a href={url} className={styles.sourceLink} target='_blank' rel='noopener noreferrer'>
															<LinkOutlined />
															{fileName}
														</a>
														<div className={styles.smallTitle}>Страница {item.page}:</div>
														<ReactMarkdown>{item.quote.replace(/^[\s\d\\n\r]+/, "")}</ReactMarkdown>
													</div>
												);
											})}
									</div>
								)}
							</div>
							<div className={styles.time}>{message?.created_at}</div>{" "}
						</>
					:	<Spin />}
				</div>
				{isBotMessage && !isStreamingPending && <Rate value={rate} onChange={value => onChange(value)} className={styles.rate} character={({index = 0}) => customIcons[index + 1]} />}
			</div>
			<div className={ClassNames(styles.avatar, (isBotMessage || isStreamingPending) && styles.botAvatar)}></div>
		</div>
	);
};

export default Message;
